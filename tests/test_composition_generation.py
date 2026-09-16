from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from mercury.composition.contracts import (
    MAX_COMPOSITION_CANDIDATES,
    MAX_COMPOSITION_NODES,
    CertifiedTopology,
    CompositionGenerationPolicy,
    CompositionProvenanceReference,
    CompositionResultStatus,
    CompositionRole,
    CompositionValidity,
)
from mercury.composition.generation import (
    CompositionGenerationRequest,
    generate_compositions,
    merge_duplicate_drafts,
    semantic_candidate_signature,
)
from mercury.composition.instantiation import (
    CompositionInstantiationRequest,
    CompositionRoleRequirement,
    instantiate_composition_candidates,
)
from mercury.contracts.workload_request import WorkloadRequest
from mercury.gateway.constraints import canonicalize_gateway_constraints
from mercury.gateway.identity import GatewayIdentity
from mercury.gateway.models import GatewayRequestEnvelope, GatewayValidationEvidence, GatewayValidationStatus
from mercury.gateway.normalization import normalize_gateway_request
from mercury.graph.models import ExecutionGraph, ExecutionGraphEdge, ExecutionGraphNode, GraphDependencyType, GraphNodeType
from mercury.graph.readiness import GraphReadinessEvidence, GraphReadinessResult, GraphReadinessStatus
from mercury.intelligence.models import ComputationalCapability, Evidence
from mercury.intelligence.pipeline import analyze_workload
from mercury.models.capabilities import CapabilityProvenance, ModelCapabilityRecord, ModelModality, ReasoningCapability
from mercury.models.compatibility import ModelCapabilityRequirements
from mercury.models.evidence import (
    CapabilityEvidence,
    CapabilityEvidenceAssessmentRequirements,
    CapabilityEvidenceKind,
    CapabilityEvidenceState,
    assess_capability_evidence,
)
from mercury.models.registry import ModelCapabilityRegistry


def pipeline():
    workload = WorkloadRequest(
        workload_id="workload-1", session_id="session-1", task_type="inference",
        input={"text": "hello"}, context={}, latency_target_ms=100.0,
        quality_target=0.9, cost_budget=None, privacy_level="confidential",
        priority=50, hardware_constraints=(),
    )
    identity = GatewayIdentity(request_id="request-1", workload_id="workload-1", session_id="session-1")
    envelope = GatewayRequestEnvelope(
        gateway_request_id="gateway-request-1", identity=identity,
        workload_request=workload, received_at=datetime(2026, 9, 17, tzinfo=UTC),
        normalized=False, validation_status=GatewayValidationStatus.ACCEPTED,
        validation_evidence=GatewayValidationEvidence(status=GatewayValidationStatus.ACCEPTED, reasons=()),
    )
    normalization = normalize_gateway_request(envelope)
    assert normalization.normalized_request is not None
    return analyze_workload(
        normalization,
        canonicalize_gateway_constraints(identity, normalization.normalized_request),
    )


def graph() -> ExecutionGraph:
    intelligence = pipeline()
    nodes = tuple(
        ExecutionGraphNode(
            node_id, node_type, f"certified {node_type.value}",
            (ComputationalCapability.GENERATION,),
            (Evidence("phase3", "certified logical stage"),),
        )
        for node_id, node_type in (
            ("input", GraphNodeType.INPUT),
            ("reasoning", GraphNodeType.REASONING),
            ("output", GraphNodeType.OUTPUT),
        )
    )
    edges = (
        ExecutionGraphEdge("input", "reasoning", GraphDependencyType.DATA, (Evidence("phase3", "logical flow"),)),
        ExecutionGraphEdge("reasoning", "output", GraphDependencyType.DATA, (Evidence("phase3", "logical flow"),)),
    )
    return ExecutionGraph(
        "graph-1", "request-1", "workload-1", "session-1", nodes, edges,
        (Evidence("phase2", "certified intelligence"),), intelligence.profile,
    )


def model(index: int, *, revision: str = "rev-1", retrieval: bool = True) -> ModelCapabilityRecord:
    return ModelCapabilityRecord(
        model_id=f"model-{index:03d}", provider=f"provider-{index:03d}",
        family="family-a", revision=revision,
        input_modalities=(ModelModality.TEXT,), output_modalities=(ModelModality.TEXT,),
        reasoning_capabilities=(ReasoningCapability.GENERAL,), supports_retrieval=retrieval,
        provenance=CapabilityProvenance(
            source="phase4", source_revision="registry-v1", evidence="certified record"
        ),
    )


def specialist_requirement() -> CompositionRoleRequirement:
    from mercury.composition.contracts import CompositionArtifactContract

    artifact = lambda artifact_id: CompositionArtifactContract(
        artifact_id=artifact_id, modalities=(ModelModality.TEXT,),
        requires_structured_output=False, evidence=("explicit artifact",),
    )
    return CompositionRoleRequirement(
        role=CompositionRole.SPECIALIST,
        requirement_ids=("specialist-retrieval",),
        requirements=ModelCapabilityRequirements(
            required_input_modalities=(ModelModality.TEXT,),
            required_output_modalities=(ModelModality.TEXT,),
            requires_retrieval=True,
            evidence=("explicit specialist requirement",),
        ),
        input_artifacts=(artifact("specialist-input"),),
        output_artifacts=(artifact("specialist-output"),),
        provenance=(
            CompositionProvenanceReference(
                source_phase="phase3", artifact_id="specialist-requirement",
                evidence="certified specialist requirement",
            ),
        ),
    )


def instantiation_request(
    count: int,
    *,
    role_requirements: tuple[CompositionRoleRequirement, ...] = (),
    composition_required: bool = False,
) -> CompositionInstantiationRequest:
    intelligence = pipeline()
    source_graph = graph()
    ready = GraphReadinessResult(
        source_graph.graph_id, source_graph.request_id, source_graph.workload_id,
        source_graph.session_id, GraphReadinessStatus.READY, (),
        (GraphReadinessEvidence("phase3", True, "certified ready graph"),),
    )
    return CompositionInstantiationRequest(
        intelligence_result=intelligence, graph=source_graph, readiness_result=ready,
        registry=ModelCapabilityRegistry(records=tuple(model(index) for index in range(count))),
        role_requirements=role_requirements, evidence_constraints=(),
        composition_required=composition_required,
    )


def generation_request(
    count: int,
    *,
    max_candidates: int = MAX_COMPOSITION_CANDIDATES,
    max_nodes: int = MAX_COMPOSITION_NODES,
    role_requirements: tuple[CompositionRoleRequirement, ...] = (),
    composition_required: bool = False,
) -> CompositionGenerationRequest:
    return CompositionGenerationRequest(
        instantiation_request=instantiation_request(
            count,
            role_requirements=role_requirements,
            composition_required=composition_required,
        ),
        policy=CompositionGenerationPolicy(
            max_nodes=max_nodes, max_candidates=max_candidates
        ),
    )


def single_drafts(count: int = 1):
    result = instantiate_composition_candidates(instantiation_request(count))
    return tuple(item for item in result.drafts if item.topology is CertifiedTopology.SINGLE)


def test_unique_candidates_remain_unique_and_canonical() -> None:
    result = generate_compositions(generation_request(3))

    assert len(result.valid_candidates) == 3
    assert len({item.composition_id for item in result.valid_candidates}) == 3
    assert result.status is CompositionResultStatus.READY
    assert result.valid_candidates == tuple(
        sorted(result.valid_candidates, key=lambda item: item.composition_id)
    )


def test_exact_semantic_duplicates_collapse_and_merge_provenance() -> None:
    original = single_drafts()[0]
    extra = CompositionProvenanceReference(
        source_phase="phase5", artifact_id="additional-source",
        evidence="additional independent source",
    )
    duplicate = original.model_copy(update={"provenance": (*original.provenance, extra)})

    merged = merge_duplicate_drafts(original, duplicate)

    assert semantic_candidate_signature(original) == semantic_candidate_signature(duplicate)
    assert extra in merged.provenance
    assert set(merged.provenance) == set(original.provenance).union(duplicate.provenance)
    assert merged.composition_id == original.composition_id


def test_duplicate_merge_preserves_evidence_assessments_and_justifications() -> None:
    original = single_drafts()[0]
    constraint = CapabilityEvidenceAssessmentRequirements(
        capability_claim="text_generation", requires_evidence=False
    )
    assessment = assess_capability_evidence(
        (
            CapabilityEvidence(
                capability_claim="text_generation", source="source-a",
                source_revision="v1", reference_id="ref-1", detail="declared evidence",
                kind=CapabilityEvidenceKind.DECLARED, state=CapabilityEvidenceState.VALID,
                supports_claim=True,
            ),
        ),
        constraint,
    )
    extra_justification = original.nodes[0].justifications[0].model_copy(
        update={"reason": "independent compatibility evidence"}
    )
    changed_node = original.nodes[0].model_copy(
        update={"justifications": (*original.nodes[0].justifications, extra_justification)}
    )
    duplicate = original.model_copy(
        update={"nodes": (changed_node,), "evidence_assessments": (assessment,)}
    )

    merged = merge_duplicate_drafts(original, duplicate)

    assert merged.evidence_assessments == (assessment,)
    assert extra_justification in merged.nodes[0].justifications


@pytest.mark.parametrize("difference", ("model", "revision", "topology", "requirements", "edges"))
def test_semantically_different_candidates_are_never_deduplicated(difference: str) -> None:
    original = single_drafts()[0]
    changed = original
    if difference in {"model", "revision"}:
        changed_record = model(99, revision="rev-2" if difference == "revision" else "rev-1")
        changed_node = original.nodes[0].model_copy(update={"model_record": changed_record})
        changed = original.model_copy(update={"nodes": (changed_node,)})
    elif difference == "topology":
        changed = original.model_copy(update={"topology": CertifiedTopology.PRIMARY_VERIFIER})
    elif difference == "requirements":
        requirements = original.nodes[0].requirements.model_copy(update={"requires_retrieval": True})
        changed_node = original.nodes[0].model_copy(update={"requirements": requirements})
        changed = original.model_copy(update={"nodes": (changed_node,)})
    else:
        changed = original.model_copy(update={"edges": (
            {
                "source_stage_id": "primary", "target_stage_id": "other",
                "dependency_type": GraphDependencyType.DATA,
                "artifact_id": "primary-output", "evidence": ("different edge",),
            },
        )})

    assert semantic_candidate_signature(original) != semantic_candidate_signature(changed)
    with pytest.raises(ValueError):
        merge_duplicate_drafts(original, changed)


def test_signature_and_merge_are_deterministic_for_equivalent_ordering() -> None:
    original = single_drafts()[0]
    reordered = original.model_copy(
        update={
            "provenance": tuple(reversed(original.provenance)),
            "evidence_assessments": tuple(reversed(original.evidence_assessments)),
        }
    )

    assert semantic_candidate_signature(original) == semantic_candidate_signature(reordered)
    assert merge_duplicate_drafts(original, reordered) == merge_duplicate_drafts(reordered, original)


def test_equivalent_registry_order_produces_identical_result() -> None:
    first_request = generation_request(3)
    records = tuple(reversed(first_request.instantiation_request.registry.records))
    second_instantiation = first_request.instantiation_request.model_copy(
        update={"registry": ModelCapabilityRegistry(records=records)}
    )
    second_request = first_request.model_copy(update={"instantiation_request": second_instantiation})

    assert generate_compositions(first_request) == generate_compositions(second_request)


def test_default_and_smaller_positive_caps_are_supported() -> None:
    assert CompositionGenerationPolicy().max_candidates == 256
    assert CompositionGenerationPolicy().max_nodes == 3
    result = generate_compositions(generation_request(2, max_candidates=1))
    assert len(result.valid_candidates) == 1


@pytest.mark.parametrize(
    ("max_nodes", "max_candidates"),
    ((0, 1), (-1, 1), (4, 1), (1, 0), (1, -1), (1, 257)),
)
def test_policy_rejects_nonpositive_or_above_certified_limits(
    max_nodes: int, max_candidates: int
) -> None:
    with pytest.raises(ValidationError):
        CompositionGenerationPolicy(max_nodes=max_nodes, max_candidates=max_candidates)


def test_under_cap_and_exactly_at_cap_are_exhaustive_not_truncated() -> None:
    under = generate_compositions(generation_request(1, max_candidates=2))
    exact = generate_compositions(generation_request(2, max_candidates=2))

    assert under.generation_metadata.truncated is False
    assert exact.generation_metadata.truncated is False
    assert under.generation_metadata.enumeration_complete is True
    assert exact.generation_metadata.enumeration_complete is True
    assert exact.generation_metadata.candidate_count_lower_bound == 2


def test_first_unique_beyond_cap_proves_transparent_lazy_truncation() -> None:
    result = generate_compositions(generation_request(3, max_candidates=2))

    assert len(result.valid_candidates) + len(result.rejected_candidates) == 2
    assert result.generation_metadata.truncated is True
    assert result.generation_metadata.enumeration_complete is False
    assert result.generation_metadata.candidate_count_lower_bound == 3
    assert result.generation_metadata.truncation_reason
    assert "canonical" in result.generation_metadata.canonical_order_description


def test_smaller_node_limit_retains_valid_and_rejected_candidates_separately() -> None:
    result = generate_compositions(
        generation_request(
            1,
            max_nodes=2,
            role_requirements=(specialist_requirement(),),
        )
    )

    assert result.status is CompositionResultStatus.READY
    assert result.valid_candidates
    assert result.rejected_candidates
    assert all(item.validity is CompositionValidity.VALID for item in result.valid_candidates)
    assert all(item.validity is CompositionValidity.REJECTED for item in result.rejected_candidates)
    assert result.generation_metadata.emitted_valid_count == len(result.valid_candidates)
    assert result.generation_metadata.emitted_rejected_count == len(result.rejected_candidates)


def test_zero_candidates_is_not_applicable_only_when_composition_is_unnecessary() -> None:
    not_applicable = generate_compositions(generation_request(0))
    failed = generate_compositions(generation_request(0, composition_required=True))

    assert not_applicable.status is CompositionResultStatus.NOT_APPLICABLE
    assert failed.status is CompositionResultStatus.FAIL
    assert failed.issues


def test_candidate_above_certified_node_limit_fails_closed() -> None:
    draft = single_drafts()[0]
    oversized = draft.model_copy(update={"nodes": (*draft.nodes, *draft.nodes, *draft.nodes, *draft.nodes)})

    with pytest.raises(ValueError):
        semantic_candidate_signature(oversized)


def test_source_and_generated_result_are_immutable() -> None:
    request = generation_request(2)
    before = request.instantiation_request.registry
    result = generate_compositions(request)

    assert request.instantiation_request.registry == before
    with pytest.raises(ValidationError):
        result.status = CompositionResultStatus.FAIL  # type: ignore[misc]
    with pytest.raises(TypeError):
        result.valid_candidates[0] = result.valid_candidates[0]  # type: ignore[index]


def test_generation_contract_exposes_no_ranking_selection_or_execution_fields() -> None:
    forbidden = {
        "rank", "score", "preference", "winner", "selected_model", "fallback",
        "cost", "latency", "quality", "hardware", "device", "placement",
        "scheduler", "runtime",
    }
    assert forbidden.isdisjoint(CompositionGenerationRequest.model_fields)
    description = generate_compositions(generation_request(1)).generation_metadata.canonical_order_description
    assert "preference" not in description.lower()
    assert "quality" not in description.lower()
