from mercury.quality_scheduler.contracts import AdmissionState
def decide_admission(*, hardware_compatible, topology_compatible, placement_eligible, hard_requirements_satisfied, evidence_sufficient, temporarily_capacity_constrained=False):
    if not evidence_sufficient: return AdmissionState.UNKNOWN,("INSUFFICIENT_EVIDENCE",)
    if not hardware_compatible or not topology_compatible or not placement_eligible or not hard_requirements_satisfied:
        return AdmissionState.REJECT,("HARD_REQUIREMENT_UNSATISFIED",)
    if temporarily_capacity_constrained: return AdmissionState.DEFER,("TEMPORARY_CAPACITY_PRESSURE",)
    return AdmissionState.ADMIT,("ALL_HARD_REQUIREMENTS_SATISFIED",)
