from mercury.quality_scheduler.contracts import PreemptionIntent
def evaluate_preemption(*,victim_workload_id,challenger_workload_id,victim_recoverable,victim_checkpointable,victim_hard_slo_safe,challenger_priority_higher):
    allowed=all((victim_recoverable,victim_checkpointable,victim_hard_slo_safe,challenger_priority_higher))
    reason=("SAFE_PREEMPTION_INTENT",) if allowed else ("PREEMPTION_NOT_SAFE",)
    return PreemptionIntent(victim_workload_id=victim_workload_id,challenger_workload_id=challenger_workload_id,allowed=allowed,reason_codes=reason)
