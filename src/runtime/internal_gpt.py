import json
import random
import time
import requests
from pathlib import Path

from .base import BaseRuntime


def load_settings():
    cfg_path = Path("config/settings.json")
    with cfg_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_prompt(name: str) -> str:
    p = Path("config/prompts") / name
    return p.read_text(encoding="utf-8")


class InternalGPTRuntime(BaseRuntime):
    def __init__(
        self,
        api_key: str,
        model: str | None = None,
        base_url: str | None = None,
        use_internal: bool = True,
    ):
        settings = load_settings()
        self.api_key = api_key
        self.model = model or settings.get("default_model", "gpt-4o")

        # Base URL (internal or external OpenAI)
        if base_url:
            self.base_url = base_url
        else:
            self.base_url = (
                settings.get("base_url_internal")
                if use_internal
                else settings.get("base_url_openai")
            )

        self.timeout = settings.get("timeout_seconds", 60)

        # Retry config (optional from settings.json)
        self.max_retries = settings.get("max_retries", 6)  # total attempts
        self.max_backoff_seconds = settings.get("max_backoff_seconds", 60)

        # Logger callback
        self.log_callback = None

    def set_logger(self, callback):
        self.log_callback = callback

    def _log(self, msg: str):
        if self.log_callback:
            self.log_callback(msg)

    def _sleep_with_backoff(self, attempt: int, retry_after: str | None):
        """
        Exponential backoff with jitter. If Retry-After header exists, prefer it.
        """
        delay = None
        if retry_after:
            try:
                delay = float(retry_after)
            except ValueError:
                delay = None

        if delay is None:
            delay = min(float(self.max_backoff_seconds), (2 ** attempt) + random.random())

        self._log(f"429/5xx: väntar {delay:.1f}s innan retry (försök {attempt + 1}/{self.max_retries})...")
        time.sleep(delay)

    def _call(self, prompt: str) -> str:
        # Log prompt
        self._log("----- PROMPT TILL MODELLEN -----")
        self._log(prompt)
        self._log("--------------------------------")

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        url = f"{self.base_url}"
        last_exc: Exception | None = None

        for attempt in range(int(self.max_retries)):
            try:
                resp = requests.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout,
                )

                # Success
                if resp.status_code < 400:
                    data = resp.json()
                    result = data["choices"][0]["message"]["content"].strip()

                    # Log response
                    self._log("----- SVAR FRÅN MODELLEN -----")
                    self._log(result)
                    self._log("--------------------------------")

                    return result

                # Retriable statuses
                if resp.status_code in (429, 500, 502, 503, 504):
                    retry_after = resp.headers.get("Retry-After")

                    self._log("----- FEL VID API-ANROP -----")
                    self._log(f"HTTP {resp.status_code} för url: {resp.url}")
                    if retry_after:
                        self._log(f"Retry-After: {retry_after}")
                    body = (resp.text or "").strip()
                    if body:
                        self._log(body[:2000])  # avoid flooding GUI
                    self._log("--------------------------------")

                    # last attempt -> raise
                    if attempt == self.max_retries - 1:
                        resp.raise_for_status()

                    self._sleep_with_backoff(attempt, retry_after)
                    continue

                # Non-retriable error
                self._log("----- FEL VID API-ANROP -----")
                self._log(f"HTTP {resp.status_code} för url: {resp.url}")
                body = (resp.text or "").strip()
                if body:
                    self._log(body[:2000])
                self._log("--------------------------------")
                resp.raise_for_status()

            except requests.RequestException as e:
                last_exc = e
                self._log("----- FEL VID API-ANROP -----")
                self._log(f"RequestException: {e}")
                self._log("--------------------------------")

                if attempt == self.max_retries - 1:
                    raise

                self._sleep_with_backoff(attempt, None)

            except Exception as e:
                # Any other exception (JSON parse, key errors, etc.)
                last_exc = e
                self._log("----- FEL VID API-ANROP -----")
                self._log(str(e))
                self._log("--------------------------------")
                raise

        # Should not reach here, but for safety:
        if last_exc:
            raise last_exc
        raise RuntimeError("Okänt fel i _call().")

    def translate(self, text: str, target_lang: str) -> str:
        tmpl = load_prompt("translate.txt")
        prompt = tmpl.format(text=text, target_lang=target_lang)

        result = self._call(prompt).strip()

        # Remove original text if included
        if text[:40].lower() in result.lower():
            result = result.replace(text, "").strip()

        # Remove common prefixes
        for prefix in ["translation:", "translated:", "output:", "result:"]:
            if result.lower().startswith(prefix):
                result = result[len(prefix):].strip()

        return result

    def infer_failure_mode(
        self,
        original_text: str,
        translated_text: str,
        dtc_codes,
        component_codes,
        sw_versions,
        dtc_entries,
    ) -> dict:
        tmpl = load_prompt("failure_mode.txt")
        prompt = tmpl.format(
            original_text=original_text,
            translated_text=translated_text,
            dtc_codes=json.dumps(dtc_codes, ensure_ascii=False),
            component_codes=json.dumps(component_codes, ensure_ascii=False),
            sw_versions=json.dumps(sw_versions, ensure_ascii=False),
            dtc_entries=json.dumps(dtc_entries, ensure_ascii=False),
        )
        raw = self._call(prompt).strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {
                "primary": raw,
                "secondary": None,
                "unrelated": [],
            }