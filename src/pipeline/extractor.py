import re
from typing import List


DTC_ALPHA_NUM = re.compile(r"\b[A-Z]{2,4}\d{3,4}\b")
DTC_NUMERIC = re.compile(r"\b\d{3,4}\b")
COMPONENT_CODE = re.compile(r"\bT\d{2,3}\b")
SW_VERSION = re.compile(r"\bSW[-_]?\d{2,4}\b", re.IGNORECASE)


def extract_dtc_codes(text: str) -> List[str]:
    if not text:
        return []
    codes = set()
    for m in DTC_ALPHA_NUM.findall(text):
        codes.add(m)
    for m in DTC_NUMERIC.findall(text):
        codes.add(m)
    return sorted(codes)


def extract_component_codes(text: str) -> List[str]:
    if not text:
        return []
    return sorted(set(COMPONENT_CODE.findall(text)))


def extract_sw_versions(text: str) -> List[str]:
    if not text:
        return []
    return sorted(set(SW_VERSION.findall(text)))
