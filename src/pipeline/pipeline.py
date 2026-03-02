from pathlib import Path
from typing import Tuple, List, Dict, Any

import pandas as pd

from .extractor import (
    extract_dtc_codes,
    extract_component_codes,
    extract_sw_versions,
)
from .dtc_lookup import load_dtc_database, lookup_dtc_entries
from .translator import translate_texts
from .failure_mode import infer_failure_modes_for_rows
from .classifier import classify_failure_mode

from ..runtime.base import BaseRuntime


def run_pipeline(
    claim_file: str,
    dtc_file: str,
    runtime: BaseRuntime,
    text_column: str = "CLAIM_TEXT_DESC",
) -> Path:
    claim_path = Path(claim_file)
    dtc_path = Path(dtc_file)

    if claim_path.suffix.lower() in [".xlsx", ".xls"]:
        df = pd.read_excel(claim_path)
    else:
        df = pd.read_csv(claim_path)

    dtc_map = load_dtc_database(str(dtc_path))

    texts: List[str] = df[text_column].fillna("").astype(str).tolist()

    dtc_codes_list: List[List[str]] = []
    component_codes_list: List[List[str]] = []
    sw_versions_list: List[List[str]] = []

    for t in texts:
        dtc_codes_list.append(extract_dtc_codes(t))
        component_codes_list.append(extract_component_codes(t))
        sw_versions_list.append(extract_sw_versions(t))

    dtc_entries_list: List[List[Dict[str, Any]]] = []
    for codes in dtc_codes_list:
        dtc_entries_list.append(lookup_dtc_entries(dtc_map, codes))

    translated_texts = translate_texts(runtime, texts)

    failure_modes = infer_failure_modes_for_rows(
        runtime,
        texts,
        translated_texts,
        dtc_codes_list,
        component_codes_list,
        sw_versions_list,
        dtc_entries_list,
    )

    df["translated_text"] = translated_texts
    df["dtc_codes"] = [", ".join(c) for c in dtc_codes_list]
    df["component_codes"] = [", ".join(c) for c in component_codes_list]
    df["sw_versions"] = [", ".join(c) for c in sw_versions_list]
    df["failure_mode_primary"] = [fm.get("primary", "") for fm in failure_modes]
    df["failure_mode_secondary"] = [fm.get("secondary", "") for fm in failure_modes]
    df["failure_mode_unrelated"] = [
        ", ".join(fm.get("unrelated", []) or []) for fm in failure_modes
    ]
    df["failure_category"] = [classify_failure_mode(fm) for fm in failure_modes]

    out_dir = Path("data/output")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{claim_path.stem}_analyzed.xlsx"
    df.to_excel(out_path, index=False)
    return out_path
