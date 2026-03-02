from typing import Dict, Any


def classify_failure_mode(fm: Dict[str, Any]) -> str:
    primary = (fm.get("primary") or "").lower()

    if any(k in primary for k in ["sensor", "position sensor", "givare"]):
        return "sensor_fault"
    if any(k in primary for k in ["harness", "cable", "kabel", "wiring"]):
        return "wiring_harness_fault"
    if any(k in primary for k in ["mechanical", "obstruction", "stuck", "blocked"]):
        return "mechanical_obstruction"
    if any(k in primary for k in ["can", "communication", "timeout"]):
        return "can_communication_fault"
    if any(k in primary for k in ["eca", "actuator"]):
        return "eca_unit_fault"
    if any(k in primary for k in ["software", "sw version", "calibration"]):
        return "software_version_issue"

    return "unknown_or_noise"
