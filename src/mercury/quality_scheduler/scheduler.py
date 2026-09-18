from mercury.reasoning_budget.contracts import canonical_hash
from mercury.quality_scheduler.contracts import SchedulingDecision,AdmissionState
from mercury.quality_scheduler.priority import priority_score,classify_priority
def schedule_request(request,features,*,admission_state,selected_candidate_ids=()):
    if admission_state is AdmissionState.UNKNOWN:
        raise ValueError("UNKNOWN admission cannot produce a scheduling decision")
    selected_candidate_ids=tuple(sorted(selected_candidate_ids))
    if len(selected_candidate_ids)!=len(set(selected_candidate_ids)):
        raise ValueError("selected candidates contain duplicates")
    if any(candidate_id not in request.placement_candidate_ids for candidate_id in selected_candidate_ids):
        raise ValueError("selected candidate is not eligible for request")
    score=priority_score(features)
    generation=1
    payload={"workload_id":request.workload_id,"admission_state":admission_state.value,
             "priority_class":classify_priority(score).value,"rank_score":score,
             "selected_candidate_ids":list(selected_candidate_ids),"queue_generation":request.queue_generation,
             "decision_generation":generation,"previous_decision_id":None,
             "required_quality_floor":request.required_quality_floor,"provenance_ids":list(request.provenance_ids)}
    fingerprint=canonical_hash(payload)
    return SchedulingDecision(
        decision_id=canonical_hash({"scheduling_decision":fingerprint}),
        workload_id=request.workload_id,admission_state=admission_state,priority_class=classify_priority(score),
        rank_score=score,selected_candidate_ids=selected_candidate_ids,
        reason_codes=("QUALITY_AWARE_DETERMINISTIC_SCHEDULING",),queue_generation=request.queue_generation,
        decision_generation=generation,required_quality_floor=request.required_quality_floor,
        provenance_ids=request.provenance_ids,fingerprint=fingerprint)

def refresh_scheduling_decision(old,request,features,*,admission_state,selected_candidate_ids,queue_generation):
    if queue_generation<=old.queue_generation: raise ValueError("stale queue generation")
    updated=request.model_copy(update={"queue_generation":queue_generation})
    fresh=schedule_request(updated,features,admission_state=admission_state,selected_candidate_ids=selected_candidate_ids)
    payload=fresh.model_dump(exclude={"decision_id","fingerprint"})
    payload["decision_generation"]=old.decision_generation+1
    payload["previous_decision_id"]=old.decision_id
    identity_payload={key:(value.value if hasattr(value,"value") else list(value) if isinstance(value,tuple) else value) for key,value in payload.items() if key not in {"reason_codes"}}
    fingerprint=canonical_hash(identity_payload)
    return SchedulingDecision(**payload,fingerprint=fingerprint,decision_id=canonical_hash({"scheduling_decision":fingerprint}))
