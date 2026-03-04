"""
Extract fault codes and component codes from claim text in Excel files.

Usage:
    python -m app_extract --in input.xlsx --out output.xlsx --text-col CLAIM_TEXT_DESC
"""

import re
import pandas as pd
from typing import List, Tuple

# Regex patterns
COMP_PATTERN = re.compile(r"\bT[\s\-_]?(\d{3,})\b", re.IGNORECASE)
DTC_PATTERN = re.compile(r"\bDTC[\s\-_]?([0-9A-Fa-f]{4,6})\b")
# Prefix codes: 2-5 uppercase letters followed by 3-6 hex chars that MUST contain at least one digit
PREFIX_CODE_PATTERN = re.compile(r"\b([A-Z]{2,5})([0-9A-Fa-f]*\d[0-9A-Fa-f]{2,5})\b")
HEX_SUFFIX_PATTERN = re.compile(r"\b([0-9A-Fa-f]{3,6})[hH]\b")
DECIMAL_PATTERN = re.compile(r"\b(\d{5})\b")
RAW_HEX_4_PATTERN = re.compile(r"\b([0-9A-Fa-f]{4})\b")


def extract_codes(text: str) -> Tuple[List[str], List[str]]:
    """
    Extracts fault codes (DTC) and component codes (COMP) from text.
    Returns (dtc_list, comp_list)
    """
    if not text or not isinstance(text, str):
        return [], []
    text = text.strip()
    found = set()
    dtc_list = []
    comp_list = []
    matched = set()

    # Priority 1: DTC-prefixed codes
    for m in DTC_PATTERN.finditer(text):
        code = "DTC" + m.group(1).upper()
        if code not in found:
            dtc_list.append(code)
            found.add(code)
            matched.update(range(m.start(), m.end()))

    # Priority 2: Prefix codes (not DTC, not COMP)
    for m in PREFIX_CODE_PATTERN.finditer(text):
        prefix = m.group(1).upper()
        code = prefix + m.group(2).upper()
        if prefix == "DTC" or prefix == "T":
            continue
        # Avoid overlap
        if any(i in matched for i in range(m.start(), m.end())):
            continue
        if code not in found:
            dtc_list.append(code)
            found.add(code)
            matched.update(range(m.start(), m.end()))

    # Priority 3: Hex with h/H suffix
    for m in HEX_SUFFIX_PATTERN.finditer(text):
        code = m.group(1).upper()
        if any(i in matched for i in range(m.start(), m.end())):
            continue
        if code not in found:
            dtc_list.append(code)
            found.add(code)
            matched.update(range(m.start(), m.end()))

    # Priority 4: Decimal 5 digits
    for m in DECIMAL_PATTERN.finditer(text):
        code = m.group(1)
        if any(i in matched for i in range(m.start(), m.end())):
            continue
        if code not in found:
            dtc_list.append(code)
            found.add(code)
            matched.update(range(m.start(), m.end()))

    # Priority 5: Hex 4 digits (must contain A-F)
    for m in RAW_HEX_4_PATTERN.finditer(text):
        code = m.group(1).upper()
        if not re.search(r"[A-F]", code):
            continue
        if any(i in matched for i in range(m.start(), m.end())):
            continue
        if code not in found:
            dtc_list.append(code)
            found.add(code)
            matched.update(range(m.start(), m.end()))

    # Component codes (T123 etc)
    comp_found = set()
    for m in COMP_PATTERN.finditer(text):
        code = "T" + m.group(1)
        code = code.upper()
        if code not in comp_found and not any(i in matched for i in range(m.start(), m.end())):
            comp_list.append(code)
            comp_found.add(code)
            matched.update(range(m.start(), m.end()))

    # Deduplicate, preserve order
    dtc_list = [c for i, c in enumerate(dtc_list) if c not in dtc_list[:i]]
    comp_list = [c for i, c in enumerate(comp_list) if c not in comp_list[:i]]
    return dtc_list, comp_list


def augment_dataframe(df: pd.DataFrame, text_col: str) -> pd.DataFrame:
    """
    Adds columns for detected_language, translated_text, DTC/COMP lists and up to 5 codes each.
    """
    df = df.copy()
    dtc_lists = []
    comp_lists = []
    dtc_cols = [[] for _ in range(5)]
    comp_cols = [[] for _ in range(5)]
    langs = []
    translations = []
    for val in df[text_col]:
        dtc, comp = extract_codes(val)
        # List columns
        dtc_lists.append(",".join(dtc))
        comp_lists.append(",".join(comp))
        # Individual columns
        for i in range(5):
            dtc_cols[i].append(dtc[i] if i < len(dtc) else "")
            comp_cols[i].append(comp[i] if i < len(comp) else "")
        # Language/translation (stub)
        langs.append("unknown")
        translations.append("")
    df["detected_language"] = langs
    df["translated_text"] = translations
    df["DTC_LIST"] = dtc_lists
    df["COMP_LIST"] = comp_lists
    for i in range(5):
        df[f"DTC{i+1}"] = dtc_cols[i]
        df[f"COMP{i+1}"] = comp_cols[i]
    return df

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extract codes from claim Excel file.")
    parser.add_argument("--in", dest="input_file", required=True)
    parser.add_argument("--out", dest="output_file", required=True)
    parser.add_argument("--text-col", dest="text_col", required=True)
    args = parser.parse_args()
    df = pd.read_excel(args.input_file)
    result = augment_dataframe(df, args.text_col)
    result.to_excel(args.output_file, index=False)
    print(f"✓ Saved: {args.output_file}")
