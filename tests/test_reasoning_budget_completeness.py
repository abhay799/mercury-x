import pytest

from mercury.contracts.intelligence_requirement import (
    GenericIntelligenceRequirementEnvelope,
    RequirementEnvelopeStatus,
    make_requirement_envelope_fingerprint,
    validate_active_requirement_envelope,
)
from mercury.placement.contracts import (
    PlacementBackendKind,
    PlacementCalibrationState,
    PlacementConfidenceBand,
    PlacementPrediction,
)
from mercury.reasoning_budget.contracts import BudgetCalibrationState, ReasoningBudgetRequest
from mercury.reasoning_budget.cost import (
    DeterministicReasoningCostBackend,
    EmpiricalReasoningCostBackend,
    LearnedReasoningCostBackend,
    ReasoningCostEstimate,
)
from mercury.reasoning_budget.difficulty import DifficultyEvidence, estimate_difficulty
from mercury.reasoning_budget.integration import normalize_phase15_confidence, normalize_phase16_speculation
from mercury.reasoning_budget.quality_gain import DeterministicQualityGainBackend
from mercury.speculation.planner import build_speculation_plan


def envelope(quality=.9):
    values = dict(
        requirement_interface_id="req-interface-1", source_slo_id="slo-1",
        source_slo_version=1, source_slo_fingerprint="slo-fingerprint-1",
        status=RequirementEnvelopeStatus.ACTIVE, quality_floor=quality, confidence_floor=.8,
        hard_requirement_ids=("quality", "verification"), soft_requirement_ids=(),
        unknown_requirement_ids=(), degradation_allowed=False, provenance_ids=("policy-1",),
    )
    return GenericIntelligenceRequirementEnvelope(
        fingerprint=make_requirement_envelope_fingerprint(**values), **values
    )


def test_generic_requirement_and_reasoning_request_are_typed_and_quality_protecting():
    protected = envelope()
    assert protected.degradation_allowed is False
    ambiguous_values = protected.model_dump(exclude={"fingerprint"}) | {
        "status": RequirementEnvelopeStatus.AMBIGUOUS,
        "unknown_requirement_ids": ("unknown",),
    }
    ambiguous = GenericIntelligenceRequirementEnvelope(
        fingerprint=make_requirement_envelope_fingerprint(**ambiguous_values), **ambiguous_values
    )
    with pytest.raises(ValueError, match="UNKNOWN"):
        validate_active_requirement_envelope(ambiguous)
    request = ReasoningBudgetRequest(
        request_id="request-1", workload_id="workload-1", segment_id="segment-1",
        requirement_interface_id=protected.requirement_interface_id,
        quality_metric_id="quality.primary", quality_floor=.9, confidence_floor=.8,
        max_reasoning_steps=8, max_tokens=4096, max_compute_units=32,
        max_speculative_branches=4, verification_depth_min=1, latency_ceiling_ms=2000,
        escalation_policy_id="escalate-v1", stop_policy_id="stop-v1",
        provenance_ids=("policy-1",),
    )
    assert request.requirement_interface_id == protected.requirement_interface_id


def test_difficulty_cost_and_quality_backends_are_evidence_backed_and_honest():
    conflicting = (
        DifficultyEvidence(evidence_id="a", feature_name="complexity", normalized_value=.05,
                           operating_domain="text", provenance_ids=("p",)),
        DifficultyEvidence(evidence_id="b", feature_name="complexity", normalized_value=.95,
                           operating_domain="text", provenance_ids=("p",)),
    )
    assert estimate_difficulty(conflicting).difficulty.value == "UNKNOWN"
    cost = DeterministicReasoningCostBackend().estimate(
        steps=4, tokens=1024, verification_depth=1, speculation_width=2,
        retry_attempts=1, aggregation_units=1, evidence_ids=("cost-input",),
    )
    assert cost.retry_units > 0 and cost.aggregation_units == 1
    assert cost.backend_id and cost.backend_version and cost.operating_domain
    assert cost.calibration_state is BudgetCalibrationState.UNCALIBRATED
    assert EmpiricalReasoningCostBackend is not LearnedReasoningCostBackend
    with pytest.raises(ValueError, match="calibration"):
        ReasoningCostEstimate(
            estimate_id="bad", compute_units=1, token_units=1, verification_units=0,
            speculation_units=0, retry_units=0, aggregation_units=0,
            backend_id="empirical", backend_version="1", backend_kind="EMPIRICAL",
            operating_domain="fixture", uncertainty=.1,
            calibration_state=BudgetCalibrationState.EMPIRICALLY_CALIBRATED,
        )
    quality = DeterministicQualityGainBackend().estimate(
        difficulty="HIGH", extra_compute_units=5, evidence_ids=("quality-input",)
    )
    assert quality.calibration_state is BudgetCalibrationState.UNCALIBRATED
    assert quality.backend_id and quality.operating_domain


def test_phase15_and_phase16_adapters_reject_duck_types_and_preserve_generation_lineage():
    prediction = PlacementPrediction(
        prediction_id="prediction-1", candidate_id="candidate-1", raw_score=.5,
        confidence_band=PlacementConfidenceBand.MEDIUM,
        calibration_state=PlacementCalibrationState.UNCALIBRATED,
        backend_kind=PlacementBackendKind.DETERMINISTIC, uncertainty=1,
        hardware_profile_generation=3, topology_generation=4,
    )
    evidence = normalize_phase15_confidence(prediction)
    assert evidence.hardware_profile_generation == 3 and evidence.topology_generation == 4
    with pytest.raises(ValueError, match="typed"):
        normalize_phase15_confidence(object())

    plan = build_speculation_plan(source_segment_id="segment-1", candidate_ids=("candidate-1",), max_branches=1)
    speculation = normalize_phase16_speculation(plan)
    assert speculation.plan_fingerprint == plan.fingerprint
    with pytest.raises(ValueError, match="typed"):
        normalize_phase16_speculation(object())
