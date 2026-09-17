from mercury.reasoning_budget.contracts import canonical_hash
from mercury.quality_scheduler.contracts import SchedulingDecision,AdmissionState
from mercury.quality_scheduler.priority import priority_score,classify_priority
def schedule_request(request,features,*,admission_state,selected_candidate_ids=()):
    score=priority_score(features)
    return SchedulingDecision(
        decision_id=canonical_hash({"workload":request.workload_id,"score":score,"admission":admission_state.value}),
        workload_id=request.workload_id,admission_state=admission_state,priority_class=classify_priority(score),
        rank_score=score,selected_candidate_ids=tuple(sorted(selected_candidate_ids)),
        reason_codes=("QUALITY_AWARE_DETERMINISTIC_SCHEDULING",))
