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


class OllamaRuntime(BaseRuntime):
    def __init__(self, model: str):
        settings = load_settings()
        self.model = model
        self.host = settings.get("ollama_host", "http://localhost:11434")
        self.timeout = settings.get("timeout_seconds", 60)
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
            "stream": False,
        }

        try:
            resp = requests.post(
                f"{self.host}/api/generate",
                json=payload,
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
                result = result[len(prefix):].strip()

        return result
