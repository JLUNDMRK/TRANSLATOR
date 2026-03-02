from typing import Dict, Any, List

from ..runtime.base import BaseRuntime


def infer_failure_modes_for_rows(
    runtime: BaseRuntime,
    original_texts: List[str],
    translated_texts: List[str],
    dtc_codes_list: List[List[str]],
    component_codes_list: List[List[str]],
    sw_versions_list: List[List[str]],
    dtc_entries_list: List[List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for orig, trans, dtc_codes, comp_codes, sws, dtc_entries in zip(
        original_texts,
        translated_texts,
        dtc_codes_list,
        component_codes_list,
        sw_versions_list,
        dtc_entries_list,
    ):
        fm = runtime.infer_failure_mode(
            original_text=orig or "",
            translated_text=trans or "",
            dtc_codes=dtc_codes,
            component_codes=comp_codes,
            sw_versions=sws,
            dtc_entries=dtc_entries,
        )
        results.append(fm)
    return results
