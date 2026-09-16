from dataclasses import fields, replace
from datetime import UTC, datetime

import pytest

from mercury.contracts.workload_request import WorkloadRequest
from mercury.gateway.constraints import canonicalize_gateway_constraints
from mercury.gateway.identity import GatewayIdentity
from mercury.gateway.models import GatewayRequestEnvelope, GatewayValidationEvidence, GatewayValidationStatus
from mercury.gateway.normalization import normalize_gateway_request
from mercury.intelligence.calibration import CalibrationStatus, calibrate_workload_intelligence
from mercury.intelligence.inference import infer_workload_intelligence
from mercury.intelligence.models import (
    ComputationalCapability, Evidence, LatencySensitivity, PrivacyRequirement,
    QualityRequirement, ReasoningComplexity, WorkloadIntelligenceProfile, WorkloadModality,
)
from mercury.intelligence.pipeline import PipelineStatus, analyze_workload
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
    normalization = normalize_gateway_request(envelope)
    assert normalization.normalized_request is not None
    constraints = canonicalize_gateway_constraints(identity, normalization.normalized_request)
    signals = extract_workload_signals(normalization, constraints)
    return signals, infer_workload_intelligence(signals), normalization, constraints, request


@pytest.mark.parametrize("field", ["request_id", "workload_id", "session_id"])
def test_blank_identity_fails_closed(field: str) -> None:
    signals, profile, _, _, _ = source()
    object.__setattr__(signals, field, " ")
    assert calibrate_workload_intelligence(signals, profile).status is CalibrationStatus.FAIL


def test_signal_profile_and_pipeline_identity_mismatches_fail_closed() -> None:
    signals, profile, normalization, constraints, _ = source()
    assert calibrate_workload_intelligence(signals, replace(profile, session_id="other")).status is CalibrationStatus.FAIL
    assert analyze_workload(normalization, constraints.model_copy(update={"workload_id": "other"})).status is PipelineStatus.FAIL


def test_malformed_evidence_and_confidence_are_rejected_or_fail_closed() -> None:
    signals, profile, _, _, _ = source()
    evidence = Evidence("signals.content", "valid")
    object.__setattr__(evidence, "reason", " ")
    malformed = replace(profile, evidence=(evidence,))
    assert calibrate_workload_intelligence(signals, malformed).status is CalibrationStatus.FAIL
    with pytest.raises(ValueError, match="confidence"):
        replace(profile, confidence=1.1)


@pytest.mark.parametrize(
    ("input_data", "modality"),
    [({"text": "hello"}, WorkloadModality.IMAGE), ({"images": ["image-1"]}, WorkloadModality.TEXT)],
)
def test_conflicting_single_modality_profiles_fail(input_data: dict[str, object], modality: WorkloadModality) -> None:
    signals, profile, _, _, _ = source(input=input_data)
    assert calibrate_workload_intelligence(signals, replace(profile, modalities=(modality,))).status is CalibrationStatus.FAIL


def test_unjustified_multimodal_and_code_or_structured_modalities_fail() -> None:
    signals, profile, _, _, _ = source()
    for modality in (WorkloadModality.MULTIMODAL, WorkloadModality.CODE, WorkloadModality.STRUCTURED_DATA):
        assert calibrate_workload_intelligence(signals, replace(profile, modalities=(modality,))).status is CalibrationStatus.FAIL


@pytest.mark.parametrize(
    "capability",
    [ComputationalCapability.TOOL_USE, ComputationalCapability.RETRIEVAL, ComputationalCapability.VISION, ComputationalCapability.SPEECH, ComputationalCapability.CODE_EXECUTION, ComputationalCapability.STRUCTURED_OUTPUT],
)
def test_unsupported_capabilities_fail_closed(capability: ComputationalCapability) -> None:
    signals, profile, _, _, _ = source()
    changed = replace(profile, required_capabilities=tuple(sorted((*profile.required_capabilities, capability), key=lambda value: value.value)))
    assert calibrate_workload_intelligence(signals, changed).status is CalibrationStatus.FAIL


def test_unsafe_latency_quality_and_reasoning_escalations_fail() -> None:
    signals, profile, _, _, _ = source()
    absent = replace(signals, latency_constraint=None, quality_constraint=None)
    escalated = replace(profile, latency_sensitivity=LatencySensitivity.REALTIME, quality_requirement=QualityRequirement.CRITICAL, reasoning_complexity=ReasoningComplexity.DEEP)
    assert calibrate_workload_intelligence(absent, escalated).status is CalibrationStatus.FAIL


@pytest.mark.parametrize("explicit, downgraded", [(PrivacyRequirement.RESTRICTED, PrivacyRequirement.CONFIDENTIAL), (PrivacyRequirement.CONFIDENTIAL, PrivacyRequirement.INTERNAL)])
def test_explicit_privacy_cannot_be_downgraded(explicit: PrivacyRequirement, downgraded: PrivacyRequirement) -> None:
    signals, profile, _, _, _ = source(privacy_level=explicit.value)
    assert calibrate_workload_intelligence(signals, replace(profile, privacy_requirement=downgraded)).status is CalibrationStatus.FAIL


def test_contradiction_fails_with_zero_deterministic_confidence() -> None:
    signals, profile, _, _, _ = source()
    bad = replace(profile, modalities=(WorkloadModality.IMAGE,))
    first = calibrate_workload_intelligence(signals, bad)
    assert first == calibrate_workload_intelligence(signals, bad)
    assert first.calibrated_confidence == 0.0


def test_failure_handling_does_not_mutate_source_objects() -> None:
    signals, profile, normalization, constraints, request = source()
    before = (profile, normalization.model_dump(mode="python"), constraints.model_dump(mode="python"), request.model_dump(mode="python"))
    calibrate_workload_intelligence(signals, replace(profile, modalities=(WorkloadModality.IMAGE,)))
    assert (profile, normalization.model_dump(mode="python"), constraints.model_dump(mode="python"), request.model_dump(mode="python")) == before


def test_failure_and_boundary_contracts_expose_no_execution_selection_fields() -> None:
    forbidden = {"model_id", "provider", "model_family", "hardware", "cpu", "gpu", "device", "region", "placement", "scheduler", "execution_graph", "runtime_execution"}
    assert forbidden.isdisjoint({field.name for field in fields(WorkloadIntelligenceProfile)})
