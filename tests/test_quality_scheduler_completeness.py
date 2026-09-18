import pytest

from mercury.quality_scheduler.admission import evaluate_typed_admission
from mercury.quality_scheduler.backfill import BackfillCandidate, select_backfill
from mercury.quality_scheduler.contracts import (
    AdmissionState, GangRequirement, SchedulingAdmissionEvidence, SchedulingFeatures,
    SchedulingRequest,
)
from mercury.quality_scheduler.fairness import advance_fairness_state
from mercury.quality_scheduler.forecast import (
    DeterministicQueueForecastBackend, EmpiricalQueueForecastBackend,
    LearnedQueueForecastBackend, QueueForecastCalibrationState,
)
from mercury.quality_scheduler.gang import evaluate_typed_gang
from mercury.quality_scheduler.scheduler import refresh_scheduling_decision, schedule_request


def request():
    return SchedulingRequest(
        workload_id="workload-1", segment_id="segment-1",
        placement_candidate_ids=("candidate-1",), reasoning_budget_id="budget-1",
        requirement_interface_id="requirement-1", arrival_generation=1,
        queue_generation=1, tenant_id="tenant-1", workload_class="interactive",
        required_quality_floor=.9, required_resource_units=2,
        reasoning_budget_generation=1, placement_generation=1,
        provenance_ids=("upstream-1",),
    )


def features(age=0):
    return SchedulingFeatures(
        deadline_pressure=.5, quality_risk=.5, verification_pressure=.5, uncertainty=.5,
        budget_pressure=.5, placement_confidence=.5, logical_age=age, fairness_weight=1,
        resource_pressure=.5, locality_score=.5, fragmentation_cost=.5,
    )


def test_typed_admission_fails_closed_on_unknown_and_distinguishes_capacity_pressure():
    evidence = SchedulingAdmissionEvidence(
        hardware_compatible=True, topology_compatible=True, placement_eligible=True,
        reasoning_budget_valid=True, hard_requirements_satisfied=True,
        evidence_sufficient=False, available_resource_units=4,
        required_resource_units=2, source_ids=("hardware", "topology", "placement", "budget"),
    )
    assert evaluate_typed_admission(evidence)[0] is AdmissionState.UNKNOWN
    deferred = evidence.model_copy(update={"evidence_sufficient": True, "available_resource_units": 1})
    assert evaluate_typed_admission(deferred)[0] is AdmissionState.DEFER


def test_fairness_lifecycle_and_schedule_generation_are_immutable_and_quality_preserving():
    first = advance_fairness_state(None, workload_id="workload-1", tenant_id="tenant-1",
                                   workload_class="batch", queue_generation=1)
    second = advance_fairness_state(first, workload_id="workload-1", tenant_id="tenant-1",
                                    workload_class="batch", queue_generation=2)
    assert first.logical_age == 0 and second.logical_age == 1
    decision = schedule_request(request(), features(age=25), admission_state=AdmissionState.ADMIT,
                                selected_candidate_ids=("candidate-1",))
    assert decision.required_quality_floor == .9
    refreshed = refresh_scheduling_decision(decision, request(), features(age=26),
                                            admission_state=AdmissionState.ADMIT,
                                            selected_candidate_ids=("candidate-1",), queue_generation=2)
    assert refreshed.decision_generation == decision.decision_generation + 1
    assert refreshed.previous_decision_id == decision.decision_id
    assert decision.queue_generation == 1


def test_backfill_gang_and_forecast_boundaries_are_typed_and_fail_closed():
    safe = BackfillCandidate(workload_id="w1", duration_units=2, resource_units=1,
                             hard_requirements_satisfied=True, provenance_ids=("estimate",))
    unknown = BackfillCandidate(workload_id="w2", duration_units=None, resource_units=1,
                                hard_requirements_satisfied=True, provenance_ids=("unknown",))
    assert select_backfill((unknown, safe), protected_slack_units=3) == ("w1",)
    gang = GangRequirement(gang_id="g", required_candidate_ids=("a", "b"),
                           required_topology_domain="rack", simultaneous=True,
                           provenance_ids=("topology",))
    assert evaluate_typed_gang(gang, available_candidate_ids=("a", "b"),
                               topology_domains={"a": "rack", "b": "rack"})[0]
    assert not evaluate_typed_gang(gang, available_candidate_ids=("a",),
                                   topology_domains={"a": "rack"})[0]
    forecast = DeterministicQueueForecastBackend().forecast((request(),))
    assert forecast.calibration_state is QueueForecastCalibrationState.UNCALIBRATED
    assert forecast.backend_id and forecast.backend_version and forecast.operating_domain
    assert EmpiricalQueueForecastBackend is not LearnedQueueForecastBackend


def test_scheduler_rejects_unknown_admission_and_duplicate_queue_identity():
    with pytest.raises(ValueError, match="admission"):
        schedule_request(request(), features(), admission_state=AdmissionState.UNKNOWN)
    with pytest.raises(ValueError, match="selected"):
        schedule_request(request(), features(), admission_state=AdmissionState.ADMIT,
                         selected_candidate_ids=("candidate-1", "candidate-1"))
