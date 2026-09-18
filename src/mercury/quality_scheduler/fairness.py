def fairness_adjustment(*,logical_age,fairness_weight,starvation_ceiling=20):
    if logical_age<0 or starvation_ceiling<1: raise ValueError("invalid logical age/starvation ceiling")
    starved=logical_age>=starvation_ceiling
    boost=min(.5,logical_age/max(1,starvation_ceiling)*.25)*fairness_weight
    return round(boost,6), starved, ("STARVATION_GUARD" if starved else "AGE_FAIRNESS",)

def advance_fairness_state(previous, *, workload_id, tenant_id, workload_class, queue_generation):
    from mercury.quality_scheduler.contracts import FairnessState
    from mercury.reasoning_budget.contracts import canonical_hash
    if previous is not None:
        if type(previous) is not FairnessState or previous.workload_id!=workload_id or previous.tenant_id!=tenant_id or previous.workload_class!=workload_class:
            raise ValueError("fairness lineage mismatch")
        if queue_generation <= previous.queue_generation:
            raise ValueError("stale fairness generation")
        age=previous.logical_age+1
    else: age=0
    payload={"workload_id":workload_id,"tenant_id":tenant_id,"workload_class":workload_class,
             "logical_age":age,"queue_generation":queue_generation}
    return FairnessState(**payload,fingerprint=canonical_hash(payload))
