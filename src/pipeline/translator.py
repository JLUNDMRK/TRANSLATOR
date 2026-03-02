from typing import List

from ..runtime.base import BaseRuntime


def translate_texts(runtime: BaseRuntime, texts: List[str]) -> List[str]:
    out = []
    for t in texts:
        if not t:
            out.append("")
            continue
        out.append(runtime.translate(t))
    return out
