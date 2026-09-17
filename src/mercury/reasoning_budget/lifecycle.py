from mercury.reasoning_budget.contracts import ReasoningBudget, make_budget_id, canonical_hash
from mercury.reasoning_budget.allocation import allocate_budget

def build_reasoning_budget(request,candidate,*,generation=1):
    if candidate.expected_quality_low is not None and candidate.expected_quality_low < request.quality_floor:
        raise ValueError("candidate below hard quality floor")
    if candidate.expected_latency_ms is not None and candidate.expected_latency_ms > request.latency_ceiling_ms:
        raise ValueError("candidate above hard latency ceiling")
    allocation=allocate_budget(request,candidate)
    bid=make_budget_id(request.request_id,candidate.candidate_id,generation)
    body={"id":bid,"request":request.request_id,"candidate":candidate.candidate_id,"generation":generation,
          "allocation":allocation.model_dump(mode="json"),"quality_floor":request.quality_floor,
          "confidence_floor":request.confidence_floor,"verification_depth":candidate.verification_depth}
    return ReasoningBudget(
        reasoning_budget_id=bid,request_id=request.request_id,segment_id=request.segment_id,
        chosen_candidate_id=candidate.candidate_id,allocation=allocation,quality_floor=request.quality_floor,
        confidence_floor=request.confidence_floor,verification_depth=candidate.verification_depth,
        escalation_conditions=("QUALITY_SHORTFALL","CONFIDENCE_SHORTFALL","VERIFICATION_FAILED","UNCERTAINTY_TOO_HIGH"),
        stop_conditions=("QUALITY_CONFIDENCE_VERIFICATION_SATISFIED","NO_CERTIFIED_ESCALATION_PATH"),
        calibration_state=candidate.calibration_state,generation=generation,
        evidence_ids=tuple(sorted(candidate.evidence_ids)),fingerprint=canonical_hash(body))

def refresh_reasoning_budget(old,request,candidate):
    return build_reasoning_budget(request,candidate,generation=old.generation+1)
