import pytest
from pydantic import ValidationError

from mercury.models.capabilities import CapabilityProvenance, CapabilityStatus, ModelCapabilityRecord, ModelModality, ReasoningCapability
from mercury.models.compatibility import CompatibilityStatus, ModelCapabilityRequirements, evaluate_compatibility


def model(**changes: object) -> ModelCapabilityRecord:
    values: dict[str, object] = {
        "model_id": "model-a", "provider": "provider-a", "family": "family-a", "revision": "v1",
        "input_modalities": (ModelModality.TEXT,), "output_modalities": (ModelModality.TEXT,),
        "reasoning_capabilities": (ReasoningCapability.GENERAL, ReasoningCapability.CODE),
        "supports_tool_use": True, "supports_retrieval": True, "supports_code_generation": True,
        "supports_code_understanding": True, "supports_structured_tool_arguments": True,
        "supports_tool_result_consumption": True, "supports_json_output": True,
        "supports_schema_constrained_output": True, "max_context_tokens": 8192,
        "max_output_tokens": 2048, "supports_streaming": True,
        "provenance": CapabilityProvenance(source="declared", source_revision="v1", evidence="manifest"),
    }
    values.update(changes)
    return ModelCapabilityRecord(**values)


def requirements(**changes: object) -> ModelCapabilityRequirements:
    values: dict[str, object] = {"evidence": ("logical graph requirement",)}
    values.update(changes)
    return ModelCapabilityRequirements(**values)


def test_minimal_and_multiple_explicit_requirements_are_compatible() -> None:
    result = evaluate_compatibility(model(), requirements(
        required_input_modalities=(ModelModality.TEXT,),
        required_output_modalities=(ModelModality.TEXT,),
        required_reasoning_capabilities=(ReasoningCapability.CODE,),
        requires_tool_use=True, requires_retrieval=True, requires_code_generation=True,
        requires_json_output=True, minimum_context_tokens=4096, minimum_output_tokens=512,
        requires_streaming=True, allowed_statuses=(CapabilityStatus.PRODUCTION,),
    ))
    assert result.status is CompatibilityStatus.COMPATIBLE
    assert result.issues == ()


@pytest.mark.parametrize(
    ("requirement", "model_change", "constraint"),
    [
        ({"required_input_modalities": (ModelModality.IMAGE,)}, {}, "input_modality"),
        ({"required_output_modalities": (ModelModality.STRUCTURED_DATA,)}, {}, "output_modality"),
        ({"required_reasoning_capabilities": (ReasoningCapability.PLANNING,)}, {}, "reasoning_capability"),
        ({"requires_tool_use": True}, {"supports_tool_use": False}, "tool_use"),
        ({"requires_retrieval": True}, {"supports_retrieval": False}, "retrieval"),
        ({"requires_code_generation": True}, {"supports_code_generation": False}, "code_generation"),
        ({"requires_json_output": True}, {"supports_json_output": False}, "json_output"),
        ({"requires_streaming": True}, {"supports_streaming": False}, "streaming"),
    ],
)
def test_missing_declared_capability_is_incompatible(requirement: dict[str, object], model_change: dict[str, object], constraint: str) -> None:
    result = evaluate_compatibility(model(**model_change), requirements(**requirement))
    assert result.status is CompatibilityStatus.INCOMPATIBLE
    assert result.issues[0].constraint_id == constraint
    assert result.issues[0].reason.strip()


@pytest.mark.parametrize("field", ["minimum_context_tokens", "minimum_output_tokens"])
def test_limits_fail_closed_when_unknown_or_insufficient(field: str) -> None:
    assert evaluate_compatibility(model(**{field.replace("minimum_", "max_"): None}), requirements(**{field: 1})).status is CompatibilityStatus.INCOMPATIBLE
    assert evaluate_compatibility(model(**{field.replace("minimum_", "max_"): 10}), requirements(**{field: 11})).status is CompatibilityStatus.INCOMPATIBLE
    assert evaluate_compatibility(model(**{field.replace("minimum_", "max_"): 11}), requirements(**{field: 11})).status is CompatibilityStatus.COMPATIBLE


@pytest.mark.parametrize("status", [CapabilityStatus.PLANNED, CapabilityStatus.RESEARCH, CapabilityStatus.SIMULATED, CapabilityStatus.EXPERIMENTAL])
def test_production_constraint_rejects_nonproduction_statuses(status: CapabilityStatus) -> None:
    assert evaluate_compatibility(model(status=status), requirements(allowed_statuses=(CapabilityStatus.PRODUCTION,))).status is CompatibilityStatus.INCOMPATIBLE
    assert evaluate_compatibility(model(status=CapabilityStatus.SIMULATED), requirements(allowed_statuses=(CapabilityStatus.SIMULATED,))).status is CompatibilityStatus.COMPATIBLE


def test_malformed_requirements_are_rejected_and_results_are_deterministic_and_immutable() -> None:
    with pytest.raises(ValidationError):
        requirements(evidence=(" ",))
    with pytest.raises(ValidationError):
        requirements(minimum_context_tokens=0)
    with pytest.raises(ValidationError):
        requirements(allowed_statuses=())
    requirement = requirements(required_input_modalities=(ModelModality.IMAGE, ModelModality.TEXT, ModelModality.IMAGE))
    first = evaluate_compatibility(model(), requirement)
    assert first == evaluate_compatibility(model(), requirement)
    assert requirement.required_input_modalities == (ModelModality.IMAGE, ModelModality.TEXT)
    with pytest.raises((AttributeError, TypeError, ValidationError)):
        first.status = CompatibilityStatus.COMPATIBLE
    forbidden = {"score", "rank", "winner", "selection", "cost", "latency", "hardware", "placement", "scheduler", "runtime"}
    assert not (forbidden & set(type(first).model_fields))
