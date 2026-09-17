def evaluate_escalation(*, quality_met, confidence_met, verification_passed, uncertainty_ok, branches_agree, hard_ceiling_reached):
    reasons=[]
    if not quality_met: reasons.append("QUALITY_SHORTFALL")
    if not confidence_met: reasons.append("CONFIDENCE_SHORTFALL")
    if not verification_passed: reasons.append("VERIFICATION_FAILED")
    if not uncertainty_ok: reasons.append("UNCERTAINTY_TOO_HIGH")
    if not branches_agree: reasons.append("SPECULATIVE_DISAGREEMENT")
    if hard_ceiling_reached:
        return False, tuple(sorted(set(reasons+["HARD_CEILING_REACHED"])))
    return bool(reasons), tuple(sorted(set(reasons)))

def evaluate_stop(*, quality_met, confidence_met, verification_passed, hard_ceiling_reached, escalation_available):
    if quality_met and confidence_met and verification_passed:
        return True, ("QUALITY_CONFIDENCE_VERIFICATION_SATISFIED",)
    if hard_ceiling_reached or not escalation_available:
        return True, ("NO_CERTIFIED_ESCALATION_PATH",)
    return False, ("CONTINUE_WITHIN_BUDGET",)
