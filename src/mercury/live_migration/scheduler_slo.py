
def validate_scheduler_slo(
    *, scheduler_decision_id: str, expected_scheduler_decision_id: str,
    slo_id: str, expected_slo_id: str, quality_floor: float, required_quality_floor: float
) -> tuple[bool, str]:
    if scheduler_decision_id != expected_scheduler_decision_id:
        return False, "SCHEDULER_DECISION_MISMATCH"
    if slo_id != expected_slo_id:
        return False, "SLO_MISMATCH"
    if quality_floor < required_quality_floor:
        return False, "QUALITY_FLOOR_WEAKENED"
    return True, "SCHEDULER_SLO_PRESERVED"
