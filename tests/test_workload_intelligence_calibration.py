from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime

import pytest

from mercury.contracts.workload_request import WorkloadRequest
from mercury.gateway.constraints import canonicalize_gateway_constraints
from mercury.gateway.identity import GatewayIdentity
from mercury.gateway.models import GatewayRequestEnvelope, GatewayValidationEvidence, GatewayValidationStatus
from mercury.gateway.normalization import normalize_gateway_request
from mercury.intelligence.calibration import CalibrationStatus, calibrate_workload_intelligence
from mercury.intelligence.inference import infer_workload_intelligence
from mercury.intelligence.models import ComputationalCapability, Evidence, LatencySensitivity, PrivacyRequirement, QualityRequirement, WorkloadModality
from mercury.intelligence.signals import extract_workload_signals


def source(**overrides: object):
    values: dict[str, object] = {
        "workload_id": "workload-1", "session_id": "session-1", "task_type": "inference",
        "input": {"text": "hello"}, "context": {}, "latency_target_ms": 100.0,
        "quality_target": 0.9, "cost_budget": None, "privacy_level": "confidential",
        "priority": 50, "hardware_constraints": (),
    }
    values.update(overrides)
    request = WorkloadRequest(**values)
    identity = GatewayIdentity(request_id="request-1", workload_id="workload-1", session_id="session-1")
    envelope = GatewayRequestEnvelope(
        gateway_request_id="gateway-request-1", identity=identity, workload_request=request,
        received_at=datetime(2026, 9, 16, tzinfo=UTC), normalized=False,
        validation_status=GatewayValidationStatus.ACCEPTED,
        validation_evidence=GatewayValidationEvidence(status=GatewayValidationStatus.ACCEPTED, reasons=()),
    )
    normalized = normalize_gateway_request(envelope)
    assert normalized.normalized_request is not None
    signals = extract_workload_signals(normalized, canonicalize_gateway_constraints(identity, normalized.normalized_request))
    return signals, infer_workload_intelligence(signals)


def test_fully_explicit_consistent_profile_calibrates_pass() -> None:
    signals, profile = source(input={"text": "hello", "tool_use": True, "structured_output_required": True}, context={"conversation": ["prior"], "long_context": True, "references": ["retrieval://1"]})
    assert calibrate_workload_intelligence(signals, profile).status is CalibrationStatus.PASS


def test_defaulted_evidence_produces_degraded_without_confidence_inflation() -> None:
    signals, profile = source()
    result = calibrate_workload_intelligence(signals, profile)
    assert result.status is CalibrationStatus.DEGRADED
    assert result.calibrated_confidence <= profile.confidence


def test_missing_evidence_does_not_produce_inflated_confidence() -> None:
    signals, profile = source()
    missing = replace(profile)
    object.__setattr__(missing, "evidence", ())
    result = calibrate_workload_intelligence(signals, missing)
    assert result.status is CalibrationStatus.FAIL
    assert result.calibrated_confidence <= profile.confidence


def test_confidence_is_bounded_deterministic_and_stronger_evidence_is_not_lower() -> None:
    weak_signals, weak_profile = source()
    strong_signals, strong_profile = source(input={"text": "hello", "tool_use": True}, context={"references": ["retrieval://1"]})
    weak = calibrate_workload_intelligence(weak_signals, weak_profile)
    strong = calibrate_workload_intelligence(strong_signals, strong_profile)
    assert weak == calibrate_workload_intelligence(weak_signals, weak_profile)
    assert 0.0 <= weak.calibrated_confidence <= 1.0
    assert weak.calibrated_confidence <= strong.calibrated_confidence


def test_text_only_signals_contradict_image_profile() -> None:
    signals, profile = source()
    result = calibrate_workload_intelligence(signals, replace(profile, modalities=(WorkloadModality.IMAGE,)))
    assert result.status is CalibrationStatus.FAIL


@pytest.mark.parametrize(
    "capability",
    [ComputationalCapability.TOOL_USE, ComputationalCapability.RETRIEVAL, ComputationalCapability.STRUCTURED_OUTPUT],
)
def test_unsupported_tool_retrieval_or_structured_output_capability_fails(capability: ComputationalCapability) -> None:
    signals, profile = source()
    incompatible = replace(profile, required_capabilities=tuple(sorted((*profile.required_capabilities, capability), key=lambda item: item.value)))
    assert calibrate_workload_intelligence(signals, incompatible).status is CalibrationStatus.FAIL


def test_identity_mismatch_and_malformed_evidence_fail_closed() -> None:
    signals, profile = source()
    mismatch = replace(profile, request_id="other-request")
    malformed = Evidence(source="signals.content", reason="valid")
    object.__setattr__(malformed, "reason", " ")
    bad_evidence = replace(profile, evidence=(malformed,))
    assert calibrate_workload_intelligence(signals, mismatch).status is CalibrationStatus.FAIL
    assert calibrate_workload_intelligence(signals, bad_evidence).status is CalibrationStatus.FAIL


def test_explicit_privacy_is_never_downgraded() -> None:
    signals, profile = source()
    more_restrictive = replace(profile, privacy_requirement=PrivacyRequirement.RESTRICTED)
    result = calibrate_workload_intelligence(signals, more_restrictive)
    assert result.status is not CalibrationStatus.FAIL


def test_absent_latency_or_quality_cannot_justify_realtime_or_critical() -> None:
    signals, profile = source()
    absent = replace(signals, latency_constraint=None, quality_constraint=None)
    unsafe = replace(profile, latency_sensitivity=LatencySensitivity.REALTIME, quality_requirement=QualityRequirement.CRITICAL)
    assert calibrate_workload_intelligence(absent, unsafe).status is CalibrationStatus.FAIL


def test_unsupported_reasoning_escalation_is_rejected() -> None:
    signals, profile = source()
    escalated = replace(profile, reasoning_complexity=profile.reasoning_complexity.DEEP)
    assert calibrate_workload_intelligence(signals, escalated).status is CalibrationStatus.FAIL


def test_original_inputs_and_result_collections_are_immutable() -> None:
    signals, profile = source()
    result = calibrate_workload_intelligence(signals, profile)
    assert result.profile is profile
    with pytest.raises(FrozenInstanceError):
        result.calibrated_confidence = 0.0  # type: ignore[misc]
    assert isinstance(result.decisions, tuple)
    with pytest.raises(AttributeError):
        result.decisions.append(result.decisions[0])  # type: ignore[attr-defined]


def test_calibration_reasons_are_nonblank_and_forbidden_fields_are_absent() -> None:
    signals, profile = source()
    result = calibrate_workload_intelligence(signals, profile)
    forbidden = {"model_id", "provider", "model_family", "hardware", "device", "cpu", "gpu", "region", "placement", "scheduler", "execution_graph", "runtime", "migration", "speculative_execution", "cost_optimization"}
    assert all(decision.reason.strip() for decision in result.decisions)
    assert forbidden.isdisjoint({field.name for field in fields(result)})
