from mercury.quality_scheduler.contracts import AdmissionState
from mercury.quality_scheduler.contracts import SchedulingAdmissionEvidence
def decide_admission(*, hardware_compatible, topology_compatible, placement_eligible, hard_requirements_satisfied, evidence_sufficient, temporarily_capacity_constrained=False):
    if not evidence_sufficient: return AdmissionState.UNKNOWN,("INSUFFICIENT_EVIDENCE",)
    if not hardware_compatible or not topology_compatible or not placement_eligible or not hard_requirements_satisfied:
        return AdmissionState.REJECT,("HARD_REQUIREMENT_UNSATISFIED",)
    if temporarily_capacity_constrained: return AdmissionState.DEFER,("TEMPORARY_CAPACITY_PRESSURE",)
    return AdmissionState.ADMIT,("ALL_HARD_REQUIREMENTS_SATISFIED",)

def evaluate_typed_admission(evidence):
    if type(evidence) is not SchedulingAdmissionEvidence:
        raise ValueError("typed scheduling admission evidence required")
    evidence=SchedulingAdmissionEvidence.model_validate(evidence.model_dump())
    if not evidence.evidence_sufficient:
        return AdmissionState.UNKNOWN,("INSUFFICIENT_EVIDENCE",)
    if not all((evidence.hardware_compatible,evidence.topology_compatible,evidence.placement_eligible,
                evidence.reasoning_budget_valid,evidence.hard_requirements_satisfied)):
        return AdmissionState.REJECT,("HARD_REQUIREMENT_UNSATISFIED",)
    if evidence.available_resource_units < evidence.required_resource_units:
        return AdmissionState.DEFER,("TEMPORARY_CAPACITY_PRESSURE",)
    return AdmissionState.ADMIT,("ALL_HARD_REQUIREMENTS_SATISFIED",)
