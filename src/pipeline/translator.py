from typing import List
from ..runtime.base import BaseRuntime


def translate_texts(runtime: BaseRuntime, texts: List[str], target_lang: str) -> List[str]:
    out = []

    for t in texts:
        if not t or not isinstance(t, str):
            out.append("")
            continue

        translated = runtime.translate(t, target_lang)
        out.append(translated)

    return out
