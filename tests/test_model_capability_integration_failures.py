import pytest
from pydantic import ValidationError

from mercury.models.capabilities import CapabilityProvenance, CapabilityStatus, ModelCapabilityRecord, ModelModality, ReasoningCapability
from mercury.models.compatibility import CompatibilityStatus, ModelCapabilityRequirements, evaluate_compatibility
from mercury.models.discovery import CapabilityDiscoveryQuery, discover_capabilities
from mercury.models.evidence import CapabilityEvidence, CapabilityEvidenceAssessmentRequirements, CapabilityEvidenceKind, CapabilityEvidenceState, EvidenceAssessmentStatus, assess_capability_evidence
from mercury.models.registry import ModelCapabilityRegistry


def record(model_id: str = "model-a", **changes: object) -> ModelCapabilityRecord:
    values: dict[str, object] = {
        "model_id": model_id, "provider": "provider-a", "family": "family-a", "revision": "v1",
        "input_modalities": (ModelModality.TEXT,), "output_modalities": (ModelModality.TEXT,),
        "reasoning_capabilities": (ReasoningCapability.GENERAL,), "supports_tool_use": True,
        "supports_retrieval": True, "supports_code_generation": True, "supports_json_output": True,
        "max_context_tokens": 8192, "max_output_tokens": 2048, "supports_streaming": True,
        "provenance": CapabilityProvenance(source="provider manifest", source_revision="v1", evidence="declared metadata"),
    }
    values.update(changes)
    return ModelCapabilityRecord(**values)


def requirements(**changes: object) -> ModelCapabilityRequirements:
    values: dict[str, object] = {"evidence": ("logical graph requirement",)}
    values.update(changes)
    return ModelCapabilityRequirements(**values)


def evidence(**changes: object) -> CapabilityEvidence:
    values: dict[str, object] = {
        "capability_claim": "tool_use", "source": "provider manifest", "source_revision": "v1",
        "reference_id": "manifest/tool-use", "detail": "declares function calling",
        "kind": CapabilityEvidenceKind.DECLARED, "state": CapabilityEvidenceState.VALID, "supports_claim": True,
    }
    values.update(changes)
    return CapabilityEvidence(**values)


def test_valid_capability_survives_lifecycle_with_identity_provenance_and_status_unchanged() -> None:
    source = record()
    registry = ModelCapabilityRegistry(records=(source,))
    required = requirements(requires_tool_use=True, allowed_statuses=(CapabilityStatus.PRODUCTION,))
    compatibility = evaluate_compatibility(registry.records[0], required)
    discovery = discover_capabilities(CapabilityDiscoveryQuery(registry=registry, requirements=required))
    assessment = assess_capability_evidence((evidence(),), CapabilityEvidenceAssessmentRequirements(capability_claim="tool_use", requires_evidence=True))
    assert compatibility.status is CompatibilityStatus.COMPATIBLE
    assert discovery.candidates[0].record == source
    assert discovery.candidates[0].record.provenance == source.provenance
    assert discovery.candidates[0].record.status is CapabilityStatus.PRODUCTION
    assert assessment.status is EvidenceAssessmentStatus.ACCEPTABLE


@pytest.mark.parametrize("field", ["model_id", "provider", "family", "revision", "provenance"])
def test_malformed_capability_cannot_enter_registry(field: str) -> None:
    values = {field: " "} if field != "provenance" else {field: {"source": " ", "source_revision": "v1", "evidence": "e"}}
    with pytest.raises(ValidationError):
        record(**values)


def test_contradictory_capability_metadata_is_rejected_before_registration() -> None:
    with pytest.raises(ValidationError, match="tool use"):
        record(supports_tool_use=False, supports_structured_tool_arguments=True)


@pytest.mark.parametrize(
    ("required", "changed"),
    [
        ({"required_input_modalities": (ModelModality.IMAGE,)}, {}),
        ({"required_reasoning_capabilities": (ReasoningCapability.PLANNING,)}, {}),
        ({"requires_tool_use": True}, {"supports_tool_use": False}),
        ({"requires_retrieval": True}, {"supports_retrieval": False}),
        ({"requires_code_generation": True}, {"supports_code_generation": False}),
        ({"requires_json_output": True}, {"supports_json_output": False}),
        ({"minimum_context_tokens": 9000}, {}),
        ({"minimum_output_tokens": 3000}, {}),
        ({"minimum_context_tokens": 1}, {"max_context_tokens": None}),
        ({"allowed_statuses": (CapabilityStatus.PRODUCTION,)}, {"status": CapabilityStatus.PLANNED}),
        ({"allowed_statuses": (CapabilityStatus.PRODUCTION,)}, {"status": CapabilityStatus.RESEARCH}),
        ({"allowed_statuses": (CapabilityStatus.PRODUCTION,)}, {"status": CapabilityStatus.SIMULATED}),
        ({"allowed_statuses": (CapabilityStatus.PRODUCTION,)}, {"status": CapabilityStatus.EXPERIMENTAL}),
    ],
)
def test_hard_compatibility_failure_never_becomes_discovery_candidate(required: dict[str, object], changed: dict[str, object]) -> None:
    source = record(**changed)
    hard = requirements(**required)
    registry = ModelCapabilityRegistry(records=(source,))
    assert evaluate_compatibility(source, hard).status is CompatibilityStatus.INCOMPATIBLE
    assert discover_capabilities(CapabilityDiscoveryQuery(registry=registry, requirements=hard)).candidates == ()


def test_registry_conflicts_are_not_overwritten_and_equivalent_order_is_deterministic() -> None:
    source = record()
    with pytest.raises(ValueError, match="conflicting"):
        ModelCapabilityRegistry(records=(source, record(supports_tool_use=False)))
    first, second = record("a"), record("b")
    assert ModelCapabilityRegistry(records=(first, second)) == ModelCapabilityRegistry(records=(second, first))


def test_evidence_hard_requirements_fail_closed_for_missing_stale_weak_or_conflicting_support() -> None:
    claim = CapabilityEvidenceAssessmentRequirements(capability_claim="tool_use", requires_evidence=True, requires_current_valid=True)
    assert assess_capability_evidence((), claim).status is EvidenceAssessmentStatus.INSUFFICIENT
    assert assess_capability_evidence((evidence(state=CapabilityEvidenceState.STALE),), claim).status is EvidenceAssessmentStatus.STALE
    measured = CapabilityEvidenceAssessmentRequirements(capability_claim="tool_use", requires_measured_or_observed=True)
    assert assess_capability_evidence((evidence(),), measured).status is EvidenceAssessmentStatus.INSUFFICIENT
    assert assess_capability_evidence((evidence(kind=CapabilityEvidenceKind.SIMULATED),), measured).status is EvidenceAssessmentStatus.INSUFFICIENT
    conflict = assess_capability_evidence((evidence(reference_id="yes"), evidence(reference_id="no", supports_claim=False)), CapabilityEvidenceAssessmentRequirements(capability_claim="tool_use", reject_conflicts=True))
    assert conflict.status is EvidenceAssessmentStatus.CONFLICTING


def test_evidence_and_requirements_are_strict_deterministic_and_immutable() -> None:
    with pytest.raises(ValidationError):
        evidence(source=" ")
    with pytest.raises(ValidationError):
        CapabilityEvidenceAssessmentRequirements(capability_claim=" ")
    first, second = evidence(reference_id="a"), evidence(reference_id="b")
    required = CapabilityEvidenceAssessmentRequirements(capability_claim="tool_use")
    assert assess_capability_evidence((first, second), required) == assess_capability_evidence((second, first), required)
    with pytest.raises((AttributeError, TypeError, ValidationError)):
        first.source = "changed"


def test_lifecycle_inputs_outputs_and_boundary_remain_immutable_and_descriptive() -> None:
    source = record()
    hard = requirements()
    result = discover_capabilities(CapabilityDiscoveryQuery(registry=ModelCapabilityRegistry(records=(source,)), requirements=hard))
    assert source.model_id == "model-a" and hard.evidence == ("logical graph requirement",)
    with pytest.raises((AttributeError, TypeError, ValidationError)):
        result.candidates += ()
    fields = set(ModelCapabilityRecord.model_fields) | set(type(result).model_fields)
    forbidden = {"rank", "score", "winner", "selected_model", "preference", "graph_assignment", "fallback", "cost", "latency", "quality", "hardware", "placement", "scheduler", "runtime"}
    assert not (fields & forbidden)
