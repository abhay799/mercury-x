from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from mercury.graph.models import GraphDependencyType
from mercury.models.capabilities import (
    CapabilityProvenance,
    ModelCapabilityRecord,
    ModelModality,
)
from mercury.models.compatibility import ModelCapabilityRequirements
from mercury.composition.contracts import (
    COMPOSITION_SCHEMA_VERSION,
    MAX_COMPOSITION_CANDIDATES,
    MAX_COMPOSITION_NODES,
    CapabilityJustification,
    CertifiedTopology,
    CompositionArtifactContract,
    CompositionCandidate,
    CompositionCandidateDraft,
    CompositionEdge,
    CompositionGenerationMetadata,
    CompositionGenerationPolicy,
    CompositionNode,
    CompositionProvenanceReference,
    CompositionRejection,
    CompositionResult,
    CompositionResultStatus,
    CompositionRole,
    CompositionValidity,
    canonical_model_identity,
)


def model_record(model_id: str = "model-a", revision: str = "rev-1") -> ModelCapabilityRecord:
    return ModelCapabilityRecord(
        model_id=model_id,
        provider="provider-a",
        family="family-a",
        revision=revision,
        input_modalities=(ModelModality.TEXT,),
        output_modalities=(ModelModality.TEXT,),
        provenance=CapabilityProvenance(
            source="phase4-registry",
            source_revision="registry-v1",
            evidence="certified registry record",
        ),
    )


def requirements() -> ModelCapabilityRequirements:
    return ModelCapabilityRequirements(
        required_input_modalities=(ModelModality.TEXT,),
        required_output_modalities=(ModelModality.TEXT,),
        evidence=("execution graph requires text generation",),
    )


def provenance(artifact_id: str = "registry-1") -> CompositionProvenanceReference:
    return CompositionProvenanceReference(
        source_phase="phase4", artifact_id=artifact_id, evidence="certified source"
    )


def artifact(artifact_id: str) -> CompositionArtifactContract:
    return CompositionArtifactContract(
        artifact_id=artifact_id,
        modalities=(ModelModality.TEXT,),
        requires_structured_output=False,
        evidence=("logical handoff contract",),
    )


def node(
    stage_id: str,
    role: CompositionRole = CompositionRole.PRIMARY,
    record: ModelCapabilityRecord | None = None,
) -> CompositionNode:
    return CompositionNode(
        stage_id=stage_id,
        role=role,
        model_record=record or model_record(),
        requirements=requirements(),
        input_artifacts=(artifact(f"{stage_id}-input"),),
        output_artifacts=(artifact(f"{stage_id}-output"),),
        justifications=(
            CapabilityJustification(
                requirement_id="generation",
                capability_field="output_modalities",
                declared_value="text",
                reason="model declares the required text output",
            ),
        ),
        provenance=(provenance(),),
    )


def edge(source: str, target: str) -> CompositionEdge:
    return CompositionEdge(
        source_stage_id=source,
        target_stage_id=target,
        dependency_type=GraphDependencyType.DATA,
        artifact_id=f"{source}-output",
        evidence=("certified logical data handoff",),
    )


def draft(**changes: Any) -> CompositionCandidateDraft:
    values: dict[str, Any] = {
        "schema_version": COMPOSITION_SCHEMA_VERSION,
        "composition_id": "sha256:" + "a" * 64,
        "request_id": "request-1",
        "workload_id": "workload-1",
        "session_id": "session-1",
        "graph_id": "graph-1",
        "pattern_id": "pattern-single-v1",
        "topology": CertifiedTopology.SINGLE,
        "nodes": (node("primary"),),
        "edges": (),
        "satisfied_requirement_ids": ("generation",),
        "evidence_assessments": (),
        "provenance": (provenance(),),
    }
    values.update(changes)
    return CompositionCandidateDraft(**values)


def rejection(issue_id: str = "unsupported-handoff") -> CompositionRejection:
    return CompositionRejection(
        issue_id=issue_id,
        stage_id="primary",
        violated_invariant="handoff compatibility",
        reason="the required handoff is unsupported",
    )


def candidate(
    validity: CompositionValidity = CompositionValidity.VALID,
    rejection_reasons: tuple[CompositionRejection, ...] = (),
    **changes: Any,
) -> CompositionCandidate:
    values = draft(**changes).model_dump()
    return CompositionCandidate(
        **values, validity=validity, rejection_reasons=rejection_reasons
    )


def metadata(
    *, valid_count: int = 1, rejected_count: int = 0, **changes: Any
) -> CompositionGenerationMetadata:
    values: dict[str, Any] = {
        "max_nodes": 3,
        "max_candidates": 256,
        "emitted_valid_count": valid_count,
        "emitted_rejected_count": rejected_count,
        "enumeration_complete": True,
        "truncated": False,
        "truncation_reason": None,
        "candidate_count_lower_bound": valid_count + rejected_count,
        "canonical_order_description": "composition_id ascending; no preference implied",
    }
    values.update(changes)
    return CompositionGenerationMetadata(**values)


def test_locked_schema_roles_topologies_and_bounds_are_exact() -> None:
    assert COMPOSITION_SCHEMA_VERSION == "mercury.model-composition/v1"
    assert MAX_COMPOSITION_NODES == 3
    assert MAX_COMPOSITION_CANDIDATES == 256
    assert {item.name for item in CompositionRole} == {
        "PRIMARY", "SPECIALIST", "VERIFIER", "CRITIC",
        "RETRIEVAL_AUGMENTER", "TOOL_MODEL",
    }
    assert {item.name for item in CertifiedTopology} == {
        "SINGLE", "PRIMARY_VERIFIER", "PRIMARY_CRITIC",
        "PRIMARY_SPECIALIST_PRIMARY", "PRIMARY_RETRIEVAL_PRIMARY",
        "PRIMARY_TOOL_PRIMARY", "PRIMARY_SPECIALIST_VERIFIER",
    }


def test_valid_single_draft_preserves_exact_model_identity_and_is_frozen() -> None:
    record = model_record(revision="exact-revision")
    value = draft(nodes=(node("primary", record=record),))

    assert value.nodes[0].model_record is record
    assert canonical_model_identity(record) == (
        "provider-a", "family-a", "model-a", "exact-revision"
    )
    with pytest.raises(ValidationError):
        value.composition_id = "changed"  # type: ignore[misc]


def test_collections_normalize_canonically_without_mutating_inputs() -> None:
    raw_nodes = [node("verifier", CompositionRole.VERIFIER), node("primary")]
    raw_edges = [edge("primary", "verifier")]
    value = draft(
        topology=CertifiedTopology.PRIMARY_VERIFIER,
        nodes=raw_nodes,
        edges=raw_edges,
        satisfied_requirement_ids=["verification", "generation", "generation"],
        provenance=[provenance("registry-2"), provenance("registry-1")],
    )

    assert [item.stage_id for item in raw_nodes] == ["verifier", "primary"]
    assert tuple(item.stage_id for item in value.nodes) == ("primary", "verifier")
    assert value.satisfied_requirement_ids == ("generation", "verification")
    assert tuple(item.artifact_id for item in value.provenance) == (
        "registry-1", "registry-2"
    )
    assert isinstance(value.nodes, tuple) and isinstance(value.edges, tuple)


def test_valid_three_stage_dag_is_deterministic() -> None:
    nodes = (
        node("verifier", CompositionRole.VERIFIER),
        node("primary", CompositionRole.PRIMARY),
        node("specialist", CompositionRole.SPECIALIST, model_record("model-b")),
    )
    edges = (edge("specialist", "verifier"), edge("primary", "specialist"))
    first = draft(
        topology=CertifiedTopology.PRIMARY_SPECIALIST_VERIFIER,
        nodes=nodes,
        edges=edges,
    )
    second = draft(
        topology=CertifiedTopology.PRIMARY_SPECIALIST_VERIFIER,
        nodes=tuple(reversed(nodes)),
        edges=tuple(reversed(edges)),
    )

    assert first == second
    assert first.model_dump_json() == second.model_dump_json()


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [("composition_id", " "), ("request_id", ""), ("pattern_id", "\t")],
)
def test_blank_candidate_identity_is_rejected(field: str, bad_value: str) -> None:
    with pytest.raises(ValidationError):
        draft(**{field: bad_value})


def test_blank_nested_evidence_and_malformed_provenance_are_rejected() -> None:
    with pytest.raises(ValidationError):
        CompositionProvenanceReference(
            source_phase="phase4", artifact_id="registry", evidence=" "
        )
    with pytest.raises(ValidationError):
        CompositionArtifactContract(
            artifact_id="artifact", modalities=(ModelModality.TEXT,),
            requires_structured_output=False, evidence=("",)
        )


@pytest.mark.parametrize(
    "nodes,edges",
    [
        ((node("a"), node("a")), ()),
        ((node("a"), node("b")), (edge("a", "missing"),)),
        ((node("a"),), (edge("a", "a"),)),
        ((node("a"), node("b")), (edge("a", "b"), edge("b", "a"))),
        ((node("a"), node("b")), ()),
        ((node("a"), node("b"), node("c"), node("d")),
         (edge("a", "b"), edge("b", "c"), edge("c", "d"))),
    ],
)
def test_unsafe_dag_shapes_are_rejected(
    nodes: tuple[CompositionNode, ...], edges: tuple[CompositionEdge, ...]
) -> None:
    with pytest.raises(ValidationError):
        draft(nodes=nodes, edges=edges)


def test_invalid_role_and_malformed_composition_hash_are_rejected() -> None:
    with pytest.raises(ValidationError):
        node("primary").model_copy(update={"role": "leader"}).model_validate(
            {**node("primary").model_dump(), "role": "leader"}
        )
    with pytest.raises(ValidationError):
        draft(composition_id="sha256:not-a-hash")


def test_candidate_validity_and_rejections_are_consistent() -> None:
    assert candidate().rejection_reasons == ()
    rejected = candidate(CompositionValidity.REJECTED, (rejection(),))
    assert rejected.validity is CompositionValidity.REJECTED
    with pytest.raises(ValidationError):
        candidate(CompositionValidity.VALID, (rejection(),))
    with pytest.raises(ValidationError):
        candidate(CompositionValidity.REJECTED)


@pytest.mark.parametrize("max_nodes,max_candidates", [(0, 1), (4, 1), (1, 0), (1, 257)])
def test_generation_policy_enforces_locked_positive_caps(
    max_nodes: int, max_candidates: int
) -> None:
    with pytest.raises(ValidationError):
        CompositionGenerationPolicy(
            max_nodes=max_nodes, max_candidates=max_candidates
        )


def test_generation_metadata_enforces_transparent_truncation() -> None:
    complete = metadata()
    assert complete.candidate_count_lower_bound == 1
    truncated = metadata(
        valid_count=1,
        rejected_count=255,
        enumeration_complete=False,
        truncated=True,
        truncation_reason="candidate cap reached in canonical enumeration",
        candidate_count_lower_bound=257,
    )
    assert truncated.truncation_reason
    with pytest.raises(ValidationError):
        metadata(truncated=True, enumeration_complete=True, truncation_reason=None)
    with pytest.raises(ValidationError):
        metadata(candidate_count_lower_bound=2)


def test_result_separates_candidates_and_enforces_status_and_counts() -> None:
    valid = candidate()
    rejected = candidate(
        CompositionValidity.REJECTED,
        (rejection(),),
        composition_id="sha256:" + "b" * 64,
    )
    result = CompositionResult(
        status=CompositionResultStatus.READY,
        valid_candidates=(valid,),
        rejected_candidates=(rejected,),
        generation_metadata=metadata(valid_count=1, rejected_count=1),
        issues=(),
    )

    assert result.valid_candidates == (valid,)
    assert result.rejected_candidates == (rejected,)
    with pytest.raises(ValidationError):
        result.status = CompositionResultStatus.FAIL  # type: ignore[misc]
    with pytest.raises(ValidationError):
        CompositionResult(
            status=CompositionResultStatus.READY,
            valid_candidates=(), rejected_candidates=(rejected,),
            generation_metadata=metadata(valid_count=0, rejected_count=1), issues=(),
        )
    with pytest.raises(ValidationError):
        CompositionResult(
            status=CompositionResultStatus.FAIL,
            valid_candidates=(valid,), rejected_candidates=(),
            generation_metadata=metadata(), issues=(),
        )


def test_not_applicable_is_empty_and_fail_is_explainable() -> None:
    not_applicable = CompositionResult(
        status=CompositionResultStatus.NOT_APPLICABLE,
        valid_candidates=(), rejected_candidates=(),
        generation_metadata=metadata(valid_count=0), issues=(),
    )
    assert not_applicable.status is CompositionResultStatus.NOT_APPLICABLE
    failed = CompositionResult(
        status=CompositionResultStatus.FAIL,
        valid_candidates=(),
        rejected_candidates=(candidate(CompositionValidity.REJECTED, (rejection(),)),),
        generation_metadata=metadata(valid_count=0, rejected_count=1),
        issues=(),
    )
    assert failed.status is CompositionResultStatus.FAIL
    with pytest.raises(ValidationError):
        CompositionResult(
            status=CompositionResultStatus.FAIL,
            valid_candidates=(), rejected_candidates=(),
            generation_metadata=metadata(valid_count=0), issues=(),
        )


def test_draft_cannot_be_exposed_as_a_final_candidate() -> None:
    with pytest.raises(ValidationError):
        CompositionResult(
            status=CompositionResultStatus.READY,
            valid_candidates=(draft(),),
            rejected_candidates=(), generation_metadata=metadata(), issues=(),
        )


def test_contracts_expose_no_selection_graph_assignment_or_physical_fields() -> None:
    forbidden = {
        "rank", "score", "winner", "selected_model", "fallback",
        "graph_node_id", "hardware", "device", "placement", "region",
        "scheduler", "runtime", "cost", "latency", "quality",
    }
    contract_types = (
        CompositionProvenanceReference, CompositionArtifactContract,
        CapabilityJustification, CompositionNode, CompositionEdge,
        CompositionCandidateDraft, CompositionRejection, CompositionCandidate,
        CompositionGenerationPolicy, CompositionGenerationMetadata, CompositionResult,
    )
    for contract_type in contract_types:
        assert forbidden.isdisjoint(contract_type.model_fields)
