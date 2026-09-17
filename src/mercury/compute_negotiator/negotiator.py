from mercury.compute_negotiator.contracts import NegotiationDecision,NegotiationOutcome
from mercury.compute_negotiator.feasibility import FeasibilityState
from mercury.reasoning_budget.contracts import canonical_hash
def decide_negotiation(*,request,feasibility_state,offers):
    if feasibility_state is FeasibilityState.UNKNOWN:
        outcome=NegotiationOutcome.UNKNOWN; offer_id=None; approval=False; reasons=("FEASIBILITY_UNKNOWN",)
    elif feasibility_state is FeasibilityState.INFEASIBLE:
        outcome=NegotiationOutcome.REJECT; offer_id=None; approval=False; reasons=("HARD_CONSTRAINT_INFEASIBLE",)
    elif feasibility_state is FeasibilityState.FEASIBLE and offers:
        exact=[o for o in offers if not o.changed_soft_constraints]
        if exact:
            outcome=NegotiationOutcome.ACCEPT; offer_id=exact[0].offer_id; approval=False; reasons=("REQUEST_SATISFIABLE",)
        else:
            outcome=NegotiationOutcome.COUNTEROFFER; offer_id=offers[0].offer_id; approval=True; reasons=("EXPLICIT_APPROVAL_REQUIRED",)
    else:
        outcome=NegotiationOutcome.COUNTEROFFER if offers else NegotiationOutcome.REJECT
        offer_id=offers[0].offer_id if offers else None
        approval=bool(offers)
        reasons=("TEMPORARY_CAPACITY_COUNTEROFFER",) if offers else ("NO_FEASIBLE_OFFER",)
    did=canonical_hash({"request":request.request_id,"outcome":outcome.value,"offer":offer_id})
    return NegotiationDecision(decision_id=did,outcome=outcome,offer_id=offer_id,explicit_approval_required=approval,reason_codes=reasons)
