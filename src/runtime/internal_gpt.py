import json
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
        if base_url:
            self.base_url = base_url
        else:
            self.base_url = (
                settings.get("base_url_internal")
                if use_internal
                else settings.get("base_url_openai")
            )
        self.timeout = settings.get("timeout_seconds", 60)

    def _call(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        resp = requests.post(
            self.base_url,
            headers=headers,
            json=payload,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    def translate(self, text: str) -> str:
        tmpl = load_prompt("translate.txt")
        prompt = tmpl.format(text=text)
        return self._call(prompt).strip()

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
