from dataclasses import FrozenInstanceError, fields

import pytest

from mercury.intelligence.models import (
    ComputationalCapability,
    ContextMagnitude,
    ContextRequirement,
    Evidence,
    LatencySensitivity,
    PrivacyRequirement,
    QualityRequirement,
    ReasoningComplexity,
    ToolRequirement,
    WorkloadIntelligenceProfile,
    WorkloadModality,
)


def minimal_profile(**changes: object) -> WorkloadIntelligenceProfile:
    values: dict[str, object] = {
        "request_id": "request-1",
        "workload_id": "workload-1",
        "session_id": "session-1",
        "modalities": [WorkloadModality.TEXT],
        "reasoning_complexity": ReasoningComplexity.MINIMAL,
        "context_requirement": ContextRequirement(ContextMagnitude.SHORT),
        "tool_requirements": ToolRequirement(False),
        "latency_sensitivity": LatencySensitivity.BATCH,
        "quality_requirement": QualityRequirement.STANDARD,
        "privacy_requirement": PrivacyRequirement.PUBLIC,
        "required_capabilities": [ComputationalCapability.GENERATION],
        "confidence": 0.0,
        "evidence": [Evidence(source="request", reason="explicit user request")],
    }
    values.update(changes)
    return WorkloadIntelligenceProfile(**values)  # type: ignore[arg-type]


def test_valid_minimal_profile_is_frozen_and_serializable() -> None:
    profile = minimal_profile()

    assert profile.to_dict()["request_id"] == "request-1"
    assert profile.to_dict()["confidence"] == 0.0
    with pytest.raises(FrozenInstanceError):
        profile.request_id = "changed"  # type: ignore[misc]


def test_valid_multimodal_profile_normalizes_collections_deterministically() -> None:
    profile = minimal_profile(
        modalities=[WorkloadModality.VIDEO, WorkloadModality.TEXT, WorkloadModality.VIDEO],
        required_capabilities=[
            ComputationalCapability.VISION,
            ComputationalCapability.GENERATION,
            ComputationalCapability.VISION,
        ],
        tool_requirements=ToolRequirement(True, [ComputationalCapability.TOOL_USE]),
        context_requirement=ContextRequirement(ContextMagnitude.LONG, True),
        confidence=1.0,
    )

    assert profile.modalities == (WorkloadModality.TEXT, WorkloadModality.VIDEO)
    assert profile.required_capabilities == (
        ComputationalCapability.GENERATION,
        ComputationalCapability.VISION,
    )
    assert profile.to_dict()["modalities"] == ["text", "video"]
    assert profile.to_dict()["required_capabilities"] == ["generation", "vision"]


@pytest.mark.parametrize("modality", list(WorkloadModality))
def test_every_workload_modality_is_supported(modality: WorkloadModality) -> None:
    assert minimal_profile(modalities=[modality]).modalities == (modality,)


@pytest.mark.parametrize("complexity", list(ReasoningComplexity))
def test_every_reasoning_complexity_is_supported(complexity: ReasoningComplexity) -> None:
    assert minimal_profile(reasoning_complexity=complexity).reasoning_complexity is complexity


@pytest.mark.parametrize("magnitude", list(ContextMagnitude))
def test_every_context_magnitude_is_supported(magnitude: ContextMagnitude) -> None:
    requires_long_context = magnitude is ContextMagnitude.LONG
    requirement = ContextRequirement(magnitude, requires_long_context)

    assert minimal_profile(context_requirement=requirement).context_requirement is requirement


@pytest.mark.parametrize("sensitivity", list(LatencySensitivity))
def test_every_latency_sensitivity_is_supported(sensitivity: LatencySensitivity) -> None:
    assert minimal_profile(latency_sensitivity=sensitivity).latency_sensitivity is sensitivity


@pytest.mark.parametrize("quality", list(QualityRequirement))
def test_every_quality_requirement_is_supported(quality: QualityRequirement) -> None:
    assert minimal_profile(quality_requirement=quality).quality_requirement is quality


@pytest.mark.parametrize("privacy", list(PrivacyRequirement))
def test_every_privacy_requirement_is_supported(privacy: PrivacyRequirement) -> None:
    assert minimal_profile(privacy_requirement=privacy).privacy_requirement is privacy


@pytest.mark.parametrize("capability", list(ComputationalCapability))
def test_every_computational_capability_is_supported(capability: ComputationalCapability) -> None:
    assert minimal_profile(required_capabilities=[capability]).required_capabilities == (capability,)


def test_tool_requirement_requires_capabilities_only_when_execution_is_required() -> None:
    assert ToolRequirement(False).required_capabilities == ()
    assert ToolRequirement(True, [ComputationalCapability.TOOL_USE]).required_capabilities == (
        ComputationalCapability.TOOL_USE,
    )
    with pytest.raises(ValueError, match="required_capabilities"):
        ToolRequirement(True)


@pytest.mark.parametrize("identity", ["request_id", "workload_id", "session_id"])
@pytest.mark.parametrize("value", ["", "  "])
def test_blank_identity_is_rejected(identity: str, value: str) -> None:
    with pytest.raises(ValueError, match=identity):
        minimal_profile(**{identity: value})


@pytest.mark.parametrize("confidence", [-0.01, 1.01, float("nan")])
def test_out_of_bounds_confidence_is_rejected(confidence: float) -> None:
    with pytest.raises(ValueError, match="confidence"):
        minimal_profile(confidence=confidence)


def test_blank_evidence_is_rejected() -> None:
    with pytest.raises(ValueError, match="reason"):
        minimal_profile(evidence=[Evidence(source="request", reason=" ")])


def test_profile_collections_are_immutable() -> None:
    profile = minimal_profile()

    assert isinstance(profile.modalities, tuple)
    assert isinstance(profile.required_capabilities, tuple)
    assert isinstance(profile.evidence, tuple)
    with pytest.raises(AttributeError):
        profile.modalities.append(WorkloadModality.IMAGE)  # type: ignore[attr-defined]


def test_equal_inputs_have_equal_deterministic_serialization() -> None:
    first = minimal_profile(modalities=[WorkloadModality.IMAGE, WorkloadModality.TEXT])
    second = minimal_profile(modalities=[WorkloadModality.TEXT, WorkloadModality.IMAGE])

    assert first == second
    assert first.to_dict() == second.to_dict()


def test_profile_exposes_no_placement_or_execution_fields() -> None:
    forbidden = {
        "model_id", "provider", "hardware", "device", "region", "placement",
        "scheduler", "execution_graph", "runtime_execution",
    }
    profile_fields = {field.name for field in fields(WorkloadIntelligenceProfile)}

    assert forbidden.isdisjoint(profile_fields)
    assert forbidden.isdisjoint(profile.to_dict() if (profile := minimal_profile()) else {})
