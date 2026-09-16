import pytest
from pydantic import ValidationError

from mercury.models.capabilities import CapabilityProvenance, CapabilityStatus, ModelCapabilityRecord, ModelModality, ReasoningCapability
from mercury.models.compatibility import ModelCapabilityRequirements
from mercury.models.discovery import CapabilityDiscoveryQuery, discover_capabilities
from mercury.models.registry import ModelCapabilityRegistry


def record(model_id: str, **changes: object) -> ModelCapabilityRecord:
    values: dict[str, object] = {
        "model_id": model_id, "provider": "provider-a", "family": "family-a", "revision": "v1",
        "input_modalities": (ModelModality.TEXT,), "output_modalities": (ModelModality.TEXT,),
        "reasoning_capabilities": (ReasoningCapability.GENERAL,), "max_context_tokens": 8192,
        "max_output_tokens": 2048, "provenance": CapabilityProvenance(source="declared", source_revision="v1", evidence="manifest"),
    }
    values.update(changes)
    return ModelCapabilityRecord(**values)


def query(records: tuple[ModelCapabilityRecord, ...] = (), **requirements: object) -> CapabilityDiscoveryQuery:
    return CapabilityDiscoveryQuery(
        registry=ModelCapabilityRegistry(records=records),
        requirements=ModelCapabilityRequirements(evidence=("logical requirement",), **requirements),
    )


def test_empty_and_zero_candidate_discovery_are_valid_without_relaxing_requirements() -> None:
    assert discover_capabilities(query()).candidates == ()
    result = discover_capabilities(query((record("text"),), required_input_modalities=(ModelModality.IMAGE,)))
    assert result.candidates == ()
    assert result.requirements.required_input_modalities == (ModelModality.IMAGE,)


def test_compatible_candidates_preserve_identity_record_provenance_and_evidence() -> None:
    source = record("model-a", supports_tool_use=True)
    result = discover_capabilities(query((source,), requires_tool_use=True))
    candidate = result.candidates[0]
    assert candidate.record is source
    assert candidate.compatibility.record is source
    assert candidate.compatibility.requirements == result.requirements
    assert candidate.record.provenance == source.provenance
    assert candidate.compatibility.issues == ()


@pytest.mark.parametrize(
    ("requirement", "model_change"),
    [
        ({"required_input_modalities": (ModelModality.IMAGE,)}, {}),
        ({"required_output_modalities": (ModelModality.STRUCTURED_DATA,)}, {}),
        ({"required_reasoning_capabilities": (ReasoningCapability.PLANNING,)}, {}),
        ({"requires_tool_use": True}, {"supports_tool_use": False}),
        ({"requires_retrieval": True}, {"supports_retrieval": False}),
        ({"requires_code_generation": True}, {"supports_code_generation": False}),
        ({"requires_json_output": True}, {"supports_json_output": False}),
        ({"minimum_context_tokens": 9000}, {}),
        ({"minimum_output_tokens": 3000}, {}),
        ({"requires_streaming": True}, {"supports_streaming": False}),
        ({"allowed_statuses": (CapabilityStatus.PRODUCTION,)}, {"status": CapabilityStatus.RESEARCH}),
    ],
)
def test_each_hard_requirement_excludes_incompatible_records(requirement: dict[str, object], model_change: dict[str, object]) -> None:
    assert discover_capabilities(query((record("model-a", **model_change),), **requirement)).candidates == ()


def test_all_compatible_records_are_returned_in_canonical_order_without_ranking() -> None:
    first, second, incompatible = record("a"), record("b"), record("c", supports_retrieval=False)
    left = discover_capabilities(query((second, incompatible, first), requires_retrieval=False))
    right = discover_capabilities(query((first, second, incompatible), requires_retrieval=False))
    assert left == right
    assert [candidate.record.model_id for candidate in left.candidates] == ["a", "b", "c"]
    fields = set(type(left).model_fields) | set(type(left.candidates[0]).model_fields)
    forbidden = {"score", "rank", "winner", "selected", "fallback", "graph_assignment", "hardware", "placement", "scheduler", "runtime"}
    assert not (forbidden & fields)


def test_discovery_inputs_and_result_are_immutable_and_malformed_queries_fail_closed() -> None:
    source = record("model-a")
    registry = ModelCapabilityRegistry(records=(source,))
    requirement = ModelCapabilityRequirements(evidence=("logical requirement",))
    result = discover_capabilities(CapabilityDiscoveryQuery(registry=registry, requirements=requirement))
    assert registry.records == (source,)
    assert requirement.evidence == ("logical requirement",)
    with pytest.raises((AttributeError, TypeError, ValidationError)):
        result.candidates += ()
    with pytest.raises(ValueError):
        discover_capabilities("invalid")
