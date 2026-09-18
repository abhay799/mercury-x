from mercury.quality_scheduler.admission import decide_admission
from mercury.quality_scheduler.contracts import (
    AdmissionState,
    SchedulingDecision,
    SchedulingFeatures,
    SchedulingRequest,
)
from mercury.quality_scheduler.fairness import fairness_adjustment
from mercury.quality_scheduler.gang import evaluate_gang
from mercury.quality_scheduler.preemption import evaluate_preemption
from mercury.quality_scheduler.scheduler import schedule_request
from mercury.quality_scheduler.speculation_accounting import account_speculation


def _raises(operation):
    try:
        operation()
    except ValueError:
        return True
    return False


def admission():
    admitted, _ = decide_admission(
        hardware_compatible=True, topology_compatible=True, placement_eligible=True,
        hard_requirements_satisfied=True, evidence_sufficient=True,
    )
    rejected, _ = decide_admission(
        hardware_compatible=True, topology_compatible=True, placement_eligible=True,
        hard_requirements_satisfied=False, evidence_sufficient=True,
    )
    unknown, _ = decide_admission(
        hardware_compatible=True, topology_compatible=True, placement_eligible=True,
        hard_requirements_satisfied=True, evidence_sufficient=False,
    )
    deferred, _ = decide_admission(
        hardware_compatible=True, topology_compatible=True, placement_eligible=True,
        hard_requirements_satisfied=True, evidence_sufficient=True,
        temporarily_capacity_constrained=True,
    )
    ok = (
        admitted is AdmissionState.ADMIT
        and rejected is AdmissionState.REJECT
        and unknown is AdmissionState.UNKNOWN
        and deferred is AdmissionState.DEFER
    )
    return ok, "admission distinguishes ADMIT, REJECT, DEFER, and UNKNOWN"


def fairness():
    _, starved, _ = fairness_adjustment(logical_age=25, fairness_weight=1, starvation_ceiling=20)
    return starved, "starvation guard executable"


def preemption():
    intent = evaluate_preemption(
        victim_workload_id="v", challenger_workload_id="c", victim_recoverable=True,
        victim_checkpointable=True, victim_hard_slo_safe=True, challenger_priority_higher=True,
    )
    return intent.allowed, "preemption safety executable"


def gang():
    ok, _ = evaluate_gang(("a", "b"), ("a", "b"))
    return ok, "gang feasibility executable"


def speculation():
    return account_speculation(branch_count=2, phase16_limit=3, phase17_limit=2, per_branch_units=1) == 2, "speculation accounting executable"


def no_quality_degrade():
    request = SchedulingRequest(
        workload_id="workload-1", segment_id="segment-1", placement_candidate_ids=("candidate-1",),
        reasoning_budget_id="budget-1", requirement_interface_id="requirement-1", arrival_generation=1,
        queue_generation=1, tenant_id="tenant-1", workload_class="interactive",
        required_quality_floor=.9, required_resource_units=2, reasoning_budget_generation=1,
        placement_generation=1, provenance_ids=("upstream",),
    )
    features = SchedulingFeatures(
        deadline_pressure=.5, quality_risk=.5, verification_pressure=.5, uncertainty=.5,
        budget_pressure=.5, placement_confidence=.5, logical_age=0, fairness_weight=1,
        resource_pressure=.5, locality_score=.5, fragmentation_cost=.5,
    )
    decision = schedule_request(
        request, features, admission_state=AdmissionState.ADMIT, selected_candidate_ids=("candidate-1",),
    )
    preserved = decision.required_quality_floor == request.required_quality_floor
    tampered = _raises(lambda: SchedulingDecision.model_validate(
        decision.model_dump() | {"required_quality_floor": request.required_quality_floor - .1}
    ))
    return preserved and tampered, "scheduling copies the required quality floor and rejects lowered-floor identity"


def boundary():
    import inspect
    import mercury.quality_scheduler.scheduler as module
    source = inspect.getsource(module)
    return not any(token in source for token in ("execute(", "migrate(", "provision(")), "no runtime side effects"


CHECKS = {
    "admission": admission,
    "fairness": fairness,
    "preemption": preemption,
    "gang": gang,
    "speculation_accounting": speculation,
    "no_quality_degrade": no_quality_degrade,
    "no_runtime_side_effects": boundary,
}
