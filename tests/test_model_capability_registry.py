import pytest
from pydantic import ValidationError

from mercury.models.capabilities import CapabilityProvenance, CapabilityStatus, ModelCapabilityRecord, ModelModality, ReasoningCapability
from mercury.models.registry import ModelCapabilityRegistry
from mercury.registry.errors import RegistryEntryNotFoundError


def record(model_id: str = "model-a", revision: str = "v1", **changes: object) -> ModelCapabilityRecord:
    values: dict[str, object] = {
        "model_id": model_id,
        "provider": "provider-a",
        "family": "family-a",
        "revision": revision,
        "input_modalities": (ModelModality.TEXT,),
        "output_modalities": (ModelModality.TEXT,),
        "reasoning_capabilities": (ReasoningCapability.GENERAL,),
        "provenance": CapabilityProvenance(source="registry declaration", source_revision="v1", evidence="capability manifest"),
    }
    values.update(changes)
    return ModelCapabilityRecord(**values)


def test_empty_single_and_multiple_registries_preserve_capability_records() -> None:
    assert ModelCapabilityRegistry().records == ()
    first, second = record(), record("model-b")
    registry = ModelCapabilityRegistry(records=(second, first))
    assert registry.records == (first, second)
    assert registry.records[0].provenance == first.provenance
    assert registry.records[0].status is CapabilityStatus.PRODUCTION


def test_exact_identity_lookup_preserves_identity_and_revision() -> None:
    first, revised = record(revision="v1"), record(revision="v2")
    registry = ModelCapabilityRegistry(records=(first, revised))
    assert registry.lookup("provider-a", "model-a", "family-a", "v1") == first
    assert registry.lookup("provider-a", "model-a", "family-a", "v2") == revised
    with pytest.raises(RegistryEntryNotFoundError):
        registry.lookup("provider-a", "model-a", "family-a", "missing")


def test_conflicting_exact_identity_is_rejected_and_equivalent_duplicates_deduplicate() -> None:
    duplicate = record()
    assert ModelCapabilityRegistry(records=(record(), duplicate)).records == (duplicate,)
    with pytest.raises(ValueError, match="conflicting"):
        ModelCapabilityRegistry(records=(record(), record(supports_tool_use=True)))


def test_listing_filtering_and_fingerprint_are_deterministic_without_ranking() -> None:
    first = record("model-a", supports_tool_use=True)
    second = record("model-b", status=CapabilityStatus.RESEARCH, input_modalities=(ModelModality.IMAGE, ModelModality.TEXT))
    left = ModelCapabilityRegistry(records=(second, first))
    right = ModelCapabilityRegistry(records=(first, second))
    assert left == right
    assert left.fingerprint == right.fingerprint
    assert left.list_records() == (first, second)
    assert left.filter(provider="provider-a") == (first, second)
    assert left.filter(status=CapabilityStatus.RESEARCH) == (second,)
    assert left.filter(input_modality=ModelModality.IMAGE) == (second,)
    assert left.filter(declared_capability="tool_use") == (first,)
    assert left.filter(family="missing") == ()
    with pytest.raises(ValueError, match="declared_capability"):
        left.filter(declared_capability="ranking")


def test_registry_and_nested_collections_are_immutable_and_inputs_unchanged() -> None:
    source = [record()]
    registry = ModelCapabilityRegistry(records=source)
    assert source == [record()]
    with pytest.raises((AttributeError, TypeError, ValidationError)):
        registry.records += (record("other"),)
    fields = ModelCapabilityRegistry.model_fields
    forbidden = {"ranking", "selection", "workload", "graph_assignment", "hardware", "placement", "scheduler", "runtime"}
    assert not (forbidden & set(fields))
