from enum import Enum
class FeasibilityState(str,Enum):
    FEASIBLE="FEASIBLE"; TEMPORARILY_INFEASIBLE="TEMPORARILY_INFEASIBLE"; INFEASIBLE="INFEASIBLE"; UNKNOWN="UNKNOWN"
def evaluate_feasibility(*,quality_possible,verification_possible,privacy_ok,residency_ok,eligible_placements,evidence_sufficient,temporary_capacity_shortage=False):
    if not evidence_sufficient: return FeasibilityState.UNKNOWN,("INSUFFICIENT_EVIDENCE",)
    if not all((quality_possible,verification_possible,privacy_ok,residency_ok)) or eligible_placements<=0:
        return FeasibilityState.INFEASIBLE,("HARD_CONSTRAINT_INFEASIBLE",)
    if temporary_capacity_shortage:
        return FeasibilityState.TEMPORARILY_INFEASIBLE,("TEMPORARY_CAPACITY_SHORTAGE",)
    return FeasibilityState.FEASIBLE,("CERTIFIED_EXECUTION_ENVELOPE_AVAILABLE",)
