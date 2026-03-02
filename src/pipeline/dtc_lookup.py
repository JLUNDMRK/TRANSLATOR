from pathlib import Path
from typing import Dict, Any, List

import pandas as pd


def load_dtc_database(path: str) -> Dict[str, Dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"DTC file not found: {path}")

    if p.suffix.lower() in [".xlsx", ".xls"]:
        df = pd.read_excel(p)
    else:
        df = pd.read_csv(p)

    df = df.fillna("")

    dtc_map: Dict[str, Dict[str, Any]] = {}
    for _, row in df.iterrows():
        code = str(row.get("DTC No", "")).strip()
        if not code:
            continue
        dtc_map[code] = {
            "dtc_no": code,
            "resp_area": str(row.get("Resp. Area", "")),
            "heading": str(row.get("DTC Heading", "")),
            "component": str(row.get("Component", "")),
            "spn": str(row.get("SPN", "")),
            "fmi": str(row.get("FMI", "")),
            "implemented": str(row.get("Implemented", "")),
            "warning_lamp": str(row.get("Warning Lamp", "")),
            "display": str(row.get("Display", "")),
            "set_conditions": str(row.get("Set conditions", "")),
            "reset_conditions": str(row.get("Reset conditions", "")),
            "system_reactions": str(row.get("System reactions/possible effects_x000D_", "")),
            "substitute_reaction": str(row.get("Substitute reaction", "")),
        }
    return dtc_map


def lookup_dtc_entries(dtc_map: Dict[str, Dict[str, Any]], codes: List[str]) -> List[Dict[str, Any]]:
    entries = []
    for c in codes:
        if c in dtc_map:
            entries.append(dtc_map[c])
    return entries
