from dataclasses import FrozenInstanceError, fields
from datetime import UTC, datetime

import pytest

from mercury.contracts.workload_request import WorkloadRequest
from mercury.gateway.constraints import canonicalize_gateway_constraints
from mercury.gateway.identity import GatewayIdentity
from mercury.gateway.models import GatewayRequestEnvelope, GatewayValidationEvidence, GatewayValidationStatus
from mercury.gateway.normalization import normalize_gateway_request
from mercury.intelligence.inference import infer_workload_intelligence
from mercury.intelligence.models import (
    ComputationalCapability,
    LatencySensitivity,
    PrivacyRequirement,
    QualityRequirement,
    WorkloadIntelligenceProfile,
    WorkloadModality,
)
from mercury.intelligence.signals import extract_workload_signals


def signals(**overrides: object):
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
    return extract_workload_signals(normalized, canonicalize_gateway_constraints(identity, normalized.normalized_request))


def infer(**overrides: object) -> WorkloadIntelligenceProfile:
    return infer_workload_intelligence(signals(**overrides))


def test_text_only_signals_infer_text_modality() -> None:
    assert infer().modalities == (WorkloadModality.TEXT,)


def test_image_only_signals_infer_image_modality_and_vision() -> None:
    profile = infer(input={"images": ["image-1"]})
    assert profile.modalities == (WorkloadModality.IMAGE,)
    assert ComputationalCapability.VISION in profile.required_capabilities


def test_multiple_explicit_modalities_infer_multimodal() -> None:
    assert infer(input={"text": "hello", "audio": ["audio-1"]}).modalities == (WorkloadModality.MULTIMODAL,)


def test_structured_data_and_explicit_code_signals_infer_their_modalities() -> None:
    assert infer(input={"structured_data": {"a": 1}}).modalities == (WorkloadModality.STRUCTURED_DATA,)
    assert infer(task_type="code", input={"code": "print(1)"}).modalities == (WorkloadModality.CODE,)


@pytest.mark.parametrize(
    ("latency", "expected"),
    [(200.0, LatencySensitivity.REALTIME), (500.0, LatencySensitivity.INTERACTIVE), (5_000.0, LatencySensitivity.RELAXED), (20_000.0, LatencySensitivity.BATCH)],
)
def test_latency_constraint_maps_deterministically(latency: float, expected: LatencySensitivity) -> None:
    assert infer(latency_target_ms=latency).latency_sensitivity is expected


@pytest.mark.parametrize(
    ("quality", "expected"),
    [(0.4, QualityRequirement.STANDARD), (0.9, QualityRequirement.HIGH), (0.95, QualityRequirement.CRITICAL)],
)
def test_quality_constraint_maps_deterministically(quality: float, expected: QualityRequirement) -> None:
    assert infer(quality_target=quality).quality_requirement is expected


@pytest.mark.parametrize("privacy", list(PrivacyRequirement))
def test_privacy_constraint_maps_without_reduction(privacy: PrivacyRequirement) -> None:
    assert infer(privacy_level=privacy.value).privacy_requirement is privacy


def test_explicit_tool_retrieval_structured_output_and_code_execution_map_to_capabilities() -> None:
    profile = infer(input={"text": "hello", "tool_use": True, "tools": ["code_execution"], "structured_output_required": True}, context={"references": ["retrieval://1"]})
    assert {ComputationalCapability.TOOL_USE, ComputationalCapability.RETRIEVAL, ComputationalCapability.STRUCTURED_OUTPUT, ComputationalCapability.CODE_EXECUTION}.issubset(profile.required_capabilities)


def test_absent_optional_information_uses_conservative_defaults() -> None:
    profile = infer(input={"text": "hello"})
    assert profile.context_requirement.requires_long_context is False
    assert profile.quality_requirement is QualityRequirement.HIGH
    assert profile.tool_requirements.external_execution_required is False


def test_identical_signals_produce_equal_profile_and_deterministic_bounded_confidence() -> None:
    first = infer()
    second = infer()
    assert first == second
    assert 0.0 <= first.confidence <= 1.0


def test_weaker_evidence_has_no_higher_confidence_than_stronger_evidence() -> None:
    weak = infer(input={"text": "hello"})
    strong = infer(input={"text": "hello", "tool_use": True, "structured_output_required": True}, context={"references": ["retrieval://1"], "long_context": True})
    assert weak.confidence <= strong.confidence


def test_all_inferred_fields_have_nonblank_evidence() -> None:
    profile = infer()
    assert all(item.source.strip() and item.reason.strip() for item in profile.evidence)
    assert len(profile.evidence) >= 9


def test_signals_are_not_mutated_and_output_is_immutable() -> None:
    source = signals()
    before = source
    profile = infer_workload_intelligence(source)
    assert source == before
    with pytest.raises(FrozenInstanceError):
        profile.confidence = 0.0  # type: ignore[misc]


def test_missing_modality_or_malformed_identity_fails_closed() -> None:
    no_modality = signals(input={"notes": "image"})
    bad_identity = signals()
    object.__setattr__(bad_identity, "request_id", " ")
    with pytest.raises(ValueError, match="modality"):
        infer_workload_intelligence(no_modality)
    with pytest.raises(ValueError, match="identity"):
        infer_workload_intelligence(bad_identity)


def test_forbidden_execution_and_selection_fields_are_absent() -> None:
    forbidden = {"model_id", "provider", "model_family", "hardware", "device", "cpu", "gpu", "region", "placement", "scheduler", "execution_graph", "runtime", "speculative_execution", "migration", "cost_optimization"}
    assert forbidden.isdisjoint({field.name for field in fields(WorkloadIntelligenceProfile)})
