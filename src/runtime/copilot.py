import json
import requests
from pathlib import Path

from .base import BaseRuntime


# configuration helpers mirror the ones used by the other runtimes

def load_settings():
    cfg_path = Path("config/settings.json")
    with cfg_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_prompt(name: str) -> str:
    p = Path("config/prompts") / name
    return p.read_text(encoding="utf-8")


class CopilotRuntime(BaseRuntime):
    """Light wrapper around a generic Copilot‑style HTTP API.

    The implementation is intentionally very similar to the existing
    :class:`.OllamaRuntime` so you can drop this in with minimal changes.

    **NOTE**
    The actual endpoint, payload and authentication headers used by your
    Copilot provider may differ; adjust ``self.host``/``_call`` accordingly.
    You can also supply an API key which will be added as a Bearer token,
    but this class does not enforce its presence.
    """

    def __init__(self, model: str, api_key: str | None = None):
        settings = load_settings()
        self.model = model
        # fallback host; override in settings.json with "copilot_host"
        self.host = settings.get("copilot_host", "https://api.github.com/copilot")
        self.timeout = settings.get("timeout_seconds", 60)
        self.api_key = api_key
        self.log_callback = None

    def set_logger(self, callback):
        self.log_callback = callback

    def _call(self, prompt: str) -> str:
        if self.log_callback:
            self.log_callback("----- PROMPT TILL MODELLEN -----")
            self.log_callback(prompt)
            self.log_callback("--------------------------------")

        payload = {
            "model": self.model,
            "prompt": prompt,
            # Copilot APIs may require different field names – adjust here
        }

        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            resp = requests.post(
                f"{self.host}/generate",
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            result = data.get("response", "").strip()
        except Exception as e:
            if self.log_callback:
                self.log_callback("----- FEL VID API-ANROP -----")
                self.log_callback(str(e))
                self.log_callback("--------------------------------")
            raise

        if self.log_callback:
            self.log_callback("----- SVAR FRÅN MODELLEN -----")
            self.log_callback(result)
            self.log_callback("--------------------------------")

        return result

    def translate(self, text: str, target_lang: str) -> str:
        tmpl = load_prompt("translate.txt")
        prompt = tmpl.format(text=text, target_lang=target_lang)

        result = self._call(prompt).strip()

        if text[:40].lower() in result.lower():
            result = result.replace(text, "").strip()

        for prefix in ["translation:", "translated:", "output:", "result:"]:
            if result.lower().startswith(prefix):
                result = result[len(prefix) :].strip()

        return result
