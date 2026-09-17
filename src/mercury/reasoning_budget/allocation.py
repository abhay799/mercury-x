from mercury.reasoning_budget.contracts import BudgetAllocation

def allocate_budget(request, candidate):
    if candidate.compute_units > request.max_compute_units:
        raise ValueError("candidate exceeds compute ceiling")
    if candidate.verification_depth < request.verification_depth_min:
        raise ValueError("candidate below verification floor")
    total=candidate.compute_units
    verification=min(total*.2, candidate.verification_depth*1.5)
    speculation=min(total*.2, max(0,candidate.speculation_width-1)*2.0)
    escalation=total*.1
    aggregation=total*.1
    primary=max(0.0,total-verification-speculation-escalation-aggregation)
    return BudgetAllocation(
        primary_reasoning_units=round(primary,6),
        verification_units=round(verification,6),
        speculation_units=round(speculation,6),
        escalation_units=round(escalation,6),
        aggregation_units=round(aggregation,6))
