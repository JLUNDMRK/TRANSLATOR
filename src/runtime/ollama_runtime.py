import json
from pathlib import Path

import requests

from .base import BaseRuntime


def load_settings():
    cfg_path = Path("config/settings.json")
    with cfg_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_prompt(name: str) -> str:
    p = Path("config/prompts") / name
    return p.read_text(encoding="utf-8")


class OllamaRuntime(BaseRuntime):
    def __init__(self, model: str | None = None, host: str | None = None):
        settings = load_settings()
        self.model = model or settings.get("ollama_model", "qwen2.5:7b")
        self.host = host or settings.get("ollama_host", "http://localhost:11434")
        self.timeout = settings.get("timeout_seconds", 60)

    def _call(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        resp = requests.post(
            f"{self.host}/api/generate",
            json=payload,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "")

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
