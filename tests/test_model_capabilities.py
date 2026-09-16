import pytest
from pydantic import ValidationError

from mercury.models.capabilities import (
    CapabilityProvenance,
    CapabilityStatus,
    ModelCapabilityRecord,
    ModelModality,
    ReasoningCapability,
)


def minimal_record(**changes: object) -> ModelCapabilityRecord:
    values: dict[str, object] = {
        "model_id": "example-text-v1",
        "provider": "example-provider",
        "family": "example-family",
        "revision": "2026-09",
        "input_modalities": (ModelModality.TEXT,),
        "output_modalities": (ModelModality.TEXT,),
        "provenance": CapabilityProvenance(
            source="declared registry", source_revision="2026-09", evidence="provider capability declaration"
        ),
    }
    values.update(changes)
    return ModelCapabilityRecord(**values)


def test_minimal_and_full_capability_records_are_valid_and_deterministic() -> None:
    minimal = minimal_record()
    full = minimal_record(
        input_modalities=(ModelModality.IMAGE, ModelModality.TEXT, ModelModality.TEXT),
        output_modalities=(ModelModality.TEXT, ModelModality.STRUCTURED_DATA),
        reasoning_capabilities=(ReasoningCapability.CODE, ReasoningCapability.MULTI_STEP),
        supports_tool_use=True,
        supports_retrieval=True,
        supports_code_generation=True,
        supports_code_understanding=True,
        supports_structured_tool_arguments=True,
        supports_tool_result_consumption=True,
        supports_json_output=True,
        supports_schema_constrained_output=True,
        max_context_tokens=128000,
        max_output_tokens=16000,
        supports_streaming=True,
        supports_batching=True,
        supports_deterministic_seed=True,
        status=CapabilityStatus.EXPERIMENTAL,
    )
    assert minimal == minimal_record()
    assert full.input_modalities == (ModelModality.IMAGE, ModelModality.TEXT)
    assert full.to_dict()["reasoning_capabilities"] == ["code", "multi_step"]


@pytest.mark.parametrize("field", ["model_id", "provider", "family", "revision"])
def test_blank_identity_and_malformed_schema_are_rejected(field: str) -> None:
    with pytest.raises(ValidationError):
        minimal_record(**{field: " "})
    with pytest.raises(ValidationError):
        minimal_record(schema_version="invalid")


def test_modalities_and_reasoning_are_strict_and_deduplicated() -> None:
    with pytest.raises(ValidationError):
        minimal_record(input_modalities=("invalid",))
    with pytest.raises(ValidationError):
        minimal_record(reasoning_capabilities=("marketing",))
    assert minimal_record(reasoning_capabilities=(ReasoningCapability.GENERAL,)).reasoning_capabilities == (ReasoningCapability.GENERAL,)


@pytest.mark.parametrize("field", ["max_context_tokens", "max_output_tokens"])
@pytest.mark.parametrize("value", [0, -1])
def test_limits_are_positive_when_declared_and_unknown_is_not_zero(field: str, value: int) -> None:
    with pytest.raises(ValidationError):
        minimal_record(**{field: value})
    assert getattr(minimal_record(), field) is None
    assert getattr(minimal_record(**{field: 1}), field) == 1


def test_provenance_status_and_nested_values_are_validated_and_immutable() -> None:
    with pytest.raises(ValidationError):
        minimal_record(provenance=CapabilityProvenance(source=" ", source_revision="v1", evidence="evidence"))
    with pytest.raises(ValidationError):
        minimal_record(status="unsupported")
    record = minimal_record(status=CapabilityStatus.PLANNED)
    assert record.is_proven_production is False
    with pytest.raises((AttributeError, TypeError, ValidationError)):
        record.model_id = "changed"
    with pytest.raises((AttributeError, TypeError, ValidationError)):
        record.input_modalities += (ModelModality.AUDIO,)


def test_descriptive_contract_excludes_selection_and_execution_fields() -> None:
    fields = ModelCapabilityRecord.model_fields
    forbidden = {
        "ranking", "score", "selection", "candidate", "hardware", "device", "placement",
        "region", "scheduler", "runtime", "execution", "cost_optimization", "latency_optimization",
    }
    assert not (forbidden & set(fields))
    with pytest.raises(ValidationError):
        minimal_record(model_score=1)


def test_inputs_are_not_mutated_and_serialization_is_stable() -> None:
    modalities = [ModelModality.TEXT, ModelModality.IMAGE, ModelModality.TEXT]
    record = minimal_record(input_modalities=modalities)
    assert modalities == [ModelModality.TEXT, ModelModality.IMAGE, ModelModality.TEXT]
    assert record.input_modalities == (ModelModality.IMAGE, ModelModality.TEXT)
    assert record.to_dict() == ModelCapabilityRecord.model_validate(record.to_dict()).to_dict()
