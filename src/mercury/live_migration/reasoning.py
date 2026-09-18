
def validate_reasoning_state(*, budget_id: str, expected_budget_id: str, consumed_units: int, max_units: int) -> tuple[bool, str]:
    if budget_id != expected_budget_id:
        return False, "REASONING_BUDGET_MISMATCH"
    if consumed_units > max_units:
        return False, "REASONING_BUDGET_EXCEEDED"
    return True, "REASONING_STATE_PRESERVED"
