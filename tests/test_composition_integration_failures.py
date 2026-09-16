from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from mercury.composition.contracts import (
    MAX_COMPOSITION_CANDIDATES,
    CapabilityJustification,
    CertifiedTopology,
    CompositionArtifactContract,
    CompositionEdge,
    CompositionGenerationPolicy,
    CompositionProvenanceReference,
    CompositionResultStatus,
    CompositionRole,
    CompositionValidity,
    canonical_model_identity,
)
from mercury.composition.generation import (
    CompositionGenerationRequest,
    generate_compositions,
    merge_duplicate_drafts,
    semantic_candidate_signature,
)
from mercury.composition.instantiation import (
    CompositionEvidenceConstraint,
    CompositionInstantiationRequest,
    CompositionRoleRequirement,
    instantiate_composition_candidates,
)
from mercury.composition.validation import (
    CompositionValidationContext,
    CompositionValidationStatus,
    validate_composition_candidate,
)
from mercury.contracts.workload_request import WorkloadRequest
from mercury.gateway.constraints import canonicalize_gateway_constraints
from mercury.gateway.identity import GatewayIdentity
from mercury.gateway.models import (
    GatewayRequestEnvelope,
    GatewayValidationEvidence,
    GatewayValidationStatus,
)
from mercury.gateway.normalization import normalize_gateway_request
from mercury.graph.models import (
    ExecutionGraph,
    ExecutionGraphEdge,
    ExecutionGraphNode,
    GraphDependencyType,
    GraphNodeType,
)
from mercury.graph.readiness import (
    GraphReadinessEvidence,
    GraphReadinessResult,
    GraphReadinessStatus,
)
from mercury.intelligence.models import ComputationalCapability, Evidence
from mercury.intelligence.pipeline import PipelineStatus, analyze_workload
from mercury.models.capabilities import (
    CapabilityProvenance,
    ModelCapabilityRecord,
    ModelModality,
    ReasoningCapability,
)
from mercury.models.compatibility import ModelCapabilityRequirements
from mercury.models.evidence import (
    CapabilityEvidence,
    CapabilityEvidenceAssessmentRequirements,
    CapabilityEvidenceKind,
    CapabilityEvidenceState,
)
from mercury.models.registry import ModelCapabilityRegistry


def intelligence():
    workload = WorkloadRequest(
        workload_id="workload-1",
        session_id="session-1",
        task_type="inference",
        input={"text": "hello"},
        context={},
        latency_target_ms=100.0,
        quality_target=0.9,
        cost_budget=None,
        privacy_level="confidential",
        priority=50,
        hardware_constraints=(),
    )
    identity = GatewayIdentity(
        request_id="request-1", workload_id="workload-1", session_id="session-1"
    )
    envelope = GatewayRequestEnvelope(
        gateway_request_id="gateway-request-1",
        identity=identity,
        workload_request=workload,
        received_at=datetime(2026, 9, 17, tzinfo=UTC),
        normalized=False,
        validation_status=GatewayValidationStatus.ACCEPTED,
        validation_evidence=GatewayValidationEvidence(
            status=GatewayValidationStatus.ACCEPTED, reasons=()
        ),
    )
    normalization = normalize_gateway_request(envelope)
    assert normalization.normalized_request is not None
    return analyze_workload(
        normalization,
        canonicalize_gateway_constraints(identity, normalization.normalized_request),
    )


def logical_graph(*extra_types: GraphNodeType) -> ExecutionGraph:
    pipeline = intelligence()
    node_types = (
        GraphNodeType.INPUT,
        *extra_types,
        GraphNodeType.REASONING,
        GraphNodeType.OUTPUT,
    )
    nodes = tuple(
        ExecutionGraphNode(
            node_id=f"node-{index}",
            node_type=node_type,
            purpose=f"certified {node_type.value} stage",
            required_capabilities=(
                {
                    GraphNodeType.RETRIEVAL: ComputationalCapability.RETRIEVAL,
                    GraphNodeType.TOOL: ComputationalCapability.TOOL_USE,
                }.get(node_type, ComputationalCapability.GENERATION),
            ),
            evidence=(Evidence("phase3", "certified logical stage"),),
        )
        for index, node_type in enumerate(node_types)
    )
    edges = tuple(
        ExecutionGraphEdge(
            source_node_id=nodes[index].node_id,
            target_node_id=nodes[index + 1].node_id,
            dependency_type=GraphDependencyType.DATA,
            evidence=(Evidence("phase3", "certified logical flow"),),
        )
        for index in range(len(nodes) - 1)
    )
    return ExecutionGraph(
        graph_id="graph-1",
        request_id="request-1",
        workload_id="workload-1",
        session_id="session-1",
        nodes=nodes,
        edges=edges,
        provenance=(Evidence("phase2", "certified intelligence provenance"),),
        intelligence_profile=pipeline.profile,
    )


def readiness(source: ExecutionGraph) -> GraphReadinessResult:
    return GraphReadinessResult(
        graph_id=source.graph_id,
        request_id=source.request_id,
        workload_id=source.workload_id,
        session_id=source.session_id,
        status=GraphReadinessStatus.READY,
        issues=(),
        evidence=(
            GraphReadinessEvidence(
                invariant="phase3_readiness",
                passed=True,
                reason="certified logical graph is ready",
            ),
        ),
    )


def model(
    model_id: str = "model-a",
    *,
    provider: str = "provider-a",
    revision: str = "rev-1",
    modalities: tuple[ModelModality, ...] = (ModelModality.TEXT,),
    retrieval: bool = True,
    tool: bool = True,
) -> ModelCapabilityRecord:
    return ModelCapabilityRecord(
        model_id=model_id,
        provider=provider,
        family="family-a",
        revision=revision,
        input_modalities=modalities,
        output_modalities=modalities,
        reasoning_capabilities=(
            ReasoningCapability.GENERAL,
            ReasoningCapability.MULTI_STEP,
        ),
        supports_retrieval=retrieval,
        supports_tool_use=tool,
        supports_structured_tool_arguments=tool,
        supports_tool_result_consumption=tool,
        supports_code_understanding=tool,
        supports_json_output=True,
        supports_schema_constrained_output=True,
        provenance=CapabilityProvenance(
            source="phase4-registry",
            source_revision="registry-v1",
            evidence="certified capability declaration",
        ),
    )


def artifact(
    artifact_id: str,
    modality: ModelModality = ModelModality.TEXT,
    *,
    structured: bool = False,
) -> CompositionArtifactContract:
    return CompositionArtifactContract(
        artifact_id=artifact_id,
        modalities=(modality,),
        requires_structured_output=structured,
        evidence=("explicit logical artifact semantics",),
    )


def role_requirement(role: CompositionRole) -> CompositionRoleRequirement:
    return CompositionRoleRequirement(
        role=role,
        requirement_ids=(f"{role.value}-requirement",),
        requirements=ModelCapabilityRequirements(
            required_input_modalities=(ModelModality.TEXT,),
            required_output_modalities=(ModelModality.TEXT,),
            requires_retrieval=role is CompositionRole.SPECIALIST,
            evidence=(f"explicit {role.value} requirement",),
        ),
        input_artifacts=(artifact(f"{role.value}-input"),),
        output_artifacts=(artifact(f"{role.value}-output"),),
        provenance=(
            CompositionProvenanceReference(
                source_phase="phase3",
                artifact_id=f"{role.value}-requirement",
                evidence=f"certified explicit {role.value} requirement",
            ),
        ),
    )


def evidence_constraint(
    state: CapabilityEvidenceState = CapabilityEvidenceState.VALID,
    *,
    include: bool = True,
) -> CompositionEvidenceConstraint:
    evidence = (
        CapabilityEvidence(
            capability_claim="text_generation",
            source="phase4-evidence",
            source_revision="evidence-v1",
            reference_id="evidence-1",
            detail="measured text generation capability",
            kind=CapabilityEvidenceKind.MEASURED,
            state=state,
            supports_claim=True,
        ),
    ) if include else ()
    return CompositionEvidenceConstraint(
        role=CompositionRole.PRIMARY,
        capability_claim="text_generation",
        assessment_requirements=CapabilityEvidenceAssessmentRequirements(
            capability_claim="text_generation",
            requires_evidence=True,
            requires_current_valid=True,
            reject_conflicts=True,
        ),
        evidence=evidence,
    )


def topology_inputs(
    topology: CertifiedTopology,
) -> tuple[tuple[GraphNodeType, ...], tuple[CompositionRoleRequirement, ...]]:
    if topology is CertifiedTopology.PRIMARY_VERIFIER:
        return (GraphNodeType.VALIDATION,), ()
    if topology is CertifiedTopology.PRIMARY_CRITIC:
        return (), (role_requirement(CompositionRole.CRITIC),)
    if topology is CertifiedTopology.PRIMARY_SPECIALIST_PRIMARY:
        return (), (role_requirement(CompositionRole.SPECIALIST),)
    if topology is CertifiedTopology.PRIMARY_RETRIEVAL_PRIMARY:
        return (GraphNodeType.RETRIEVAL,), ()
    if topology is CertifiedTopology.PRIMARY_TOOL_PRIMARY:
        return (GraphNodeType.TOOL,), ()
    if topology is CertifiedTopology.PRIMARY_SPECIALIST_VERIFIER:
        return (
            GraphNodeType.VALIDATION,
        ), (role_requirement(CompositionRole.SPECIALIST),)
    return (), ()


def instantiation_request(
    *,
    topology: CertifiedTopology = CertifiedTopology.SINGLE,
    records: tuple[ModelCapabilityRecord, ...] | None = None,
    composition_required: bool | None = None,
    constraints: tuple[CompositionEvidenceConstraint, ...] = (),
    role_requirements: tuple[CompositionRoleRequirement, ...] | None = None,
) -> CompositionInstantiationRequest:
    extras, default_roles = topology_inputs(topology)
    source_graph = logical_graph(*extras)
    return CompositionInstantiationRequest(
        intelligence_result=intelligence(),
        graph=source_graph,
        readiness_result=readiness(source_graph),
        registry=ModelCapabilityRegistry(
            records=records if records is not None else (model(),)
        ),
        role_requirements=(
            default_roles if role_requirements is None else role_requirements
        ),
        evidence_constraints=constraints,
        composition_required=(
            topology is not CertifiedTopology.SINGLE
            if composition_required is None
            else composition_required
        ),
    )


def generation_request(
    *,
    topology: CertifiedTopology = CertifiedTopology.SINGLE,
    records: tuple[ModelCapabilityRecord, ...] | None = None,
    composition_required: bool | None = None,
    constraints: tuple[CompositionEvidenceConstraint, ...] = (),
    role_requirements: tuple[CompositionRoleRequirement, ...] | None = None,
    max_nodes: int = 3,
    max_candidates: int = MAX_COMPOSITION_CANDIDATES,
) -> CompositionGenerationRequest:
    return CompositionGenerationRequest(
        instantiation_request=instantiation_request(
            topology=topology,
            records=records,
            composition_required=composition_required,
            constraints=constraints,
            role_requirements=role_requirements,
        ),
        policy=CompositionGenerationPolicy(
            max_nodes=max_nodes, max_candidates=max_candidates
        ),
    )


def draft_and_context(topology: CertifiedTopology = CertifiedTopology.SINGLE):
    request = instantiation_request(topology=topology)
    result = instantiate_composition_candidates(request)
    draft = next(item for item in result.drafts if item.topology is topology)
    context = CompositionValidationContext(
        intelligence_result=request.intelligence_result,
        graph=request.graph,
        readiness_result=request.readiness_result,
        registry=request.registry,
        hard_requirement_ids=draft.satisfied_requirement_ids,
    )
    return draft, context


@pytest.mark.parametrize("topology", tuple(CertifiedTopology))
def test_all_certified_topologies_survive_the_complete_pipeline(
    topology: CertifiedTopology,
) -> None:
    request = generation_request(topology=topology)

    first = generate_compositions(request)
    second = generate_compositions(request)
    candidate = next(item for item in first.valid_candidates if item.topology is topology)

    assert first == second
    assert first.status is CompositionResultStatus.READY
    assert candidate.validity is CompositionValidity.VALID
    assert candidate.request_id == request.instantiation_request.intelligence_result.request_id
    assert candidate.workload_id == request.instantiation_request.graph.workload_id
    assert candidate.session_id == request.instantiation_request.readiness_result.session_id
    assert candidate.graph_id == request.instantiation_request.graph.graph_id
    assert all(
        node.model_record is request.instantiation_request.registry.records[0]
        for node in candidate.nodes
    )
    assert all(node.justifications and node.provenance for node in candidate.nodes)
    assert candidate.provenance
    assert all(item.evidence.strip() for item in candidate.provenance)


def test_failed_intelligence_blocked_readiness_and_identity_drift_fail_closed() -> None:
    valid = instantiation_request()
    failed_intelligence = replace(
        valid.intelligence_result,
        signals=None,
        profile=None,
        calibration=None,
        status=PipelineStatus.FAIL,
    )
    blocked = replace(valid.readiness_result, status=GraphReadinessStatus.BLOCKED)

    with pytest.raises(ValidationError, match="failed workload intelligence"):
        CompositionInstantiationRequest(
            **{
                **vars(valid),
                "intelligence_result": failed_intelligence,
            }
        )
    with pytest.raises(ValidationError, match="readiness"):
        CompositionInstantiationRequest(
            **{**vars(valid), "readiness_result": blocked}
        )
    for field, changed in (
        ("request_id", "request-other"),
        ("workload_id", "workload-other"),
        ("session_id", "session-other"),
        ("graph_id", "graph-other"),
    ):
        changed_readiness = replace(valid.readiness_result, **{field: changed})
        with pytest.raises(ValidationError):
            CompositionInstantiationRequest(
                **{
                    **vars(valid),
                    "readiness_result": changed_readiness,
                }
            )


def test_required_composition_fails_with_empty_or_incompatible_registry() -> None:
    empty = generate_compositions(
        generation_request(
            topology=CertifiedTopology.PRIMARY_CRITIC,
            records=(),
        )
    )
    incompatible = generate_compositions(
        generation_request(
            topology=CertifiedTopology.PRIMARY_CRITIC,
            records=(model("text-in-name", modalities=(ModelModality.IMAGE,)),),
        )
    )

    assert empty.status is CompositionResultStatus.FAIL
    assert incompatible.status is CompositionResultStatus.FAIL
    assert empty.issues and incompatible.issues


@pytest.mark.parametrize(
    "constraint",
    (
        evidence_constraint(include=False),
        evidence_constraint(CapabilityEvidenceState.STALE),
        evidence_constraint(CapabilityEvidenceState.CONFLICTING),
    ),
)
def test_missing_stale_or_conflicting_required_evidence_fails_closed(
    constraint: CompositionEvidenceConstraint,
) -> None:
    result = generate_compositions(
        generation_request(
            topology=CertifiedTopology.PRIMARY_CRITIC,
            constraints=(constraint,),
        )
    )

    assert result.status is CompositionResultStatus.FAIL
    assert result.valid_candidates == ()


def test_optional_evidence_is_not_invented_or_required() -> None:
    result = generate_compositions(generation_request())

    assert result.status is CompositionResultStatus.READY
    assert result.valid_candidates[0].evidence_assessments == ()


@pytest.mark.parametrize(
    ("defect", "issue_id"),
    (
        ("unsupported_topology", "pattern_conformance"),
        ("duplicate_stage", "dag_structure"),
        ("dangling_edge", "dag_structure"),
        ("self_edge", "dag_structure"),
        ("cycle", "dag_structure"),
        ("orphan", "dag_structure"),
    ),
)
def test_malformed_topology_and_dag_states_are_rejected_without_repair(
    defect: str, issue_id: str
) -> None:
    draft, context = draft_and_context(CertifiedTopology.PRIMARY_VERIFIER)
    changes: dict[str, object] = {}
    if defect == "unsupported_topology":
        changes["topology"] = "recursive_swarm"
    elif defect == "duplicate_stage":
        changes["nodes"] = (draft.nodes[0], draft.nodes[0])
    elif defect == "dangling_edge":
        changes["edges"] = (
            draft.edges[0].model_copy(update={"target_stage_id": "missing"}),
        )
    elif defect == "self_edge":
        changes["edges"] = (
            draft.edges[0].model_copy(
                update={"target_stage_id": draft.edges[0].source_stage_id}
            ),
        )
    elif defect == "cycle":
        changes["edges"] = (
            *draft.edges,
            CompositionEdge.model_construct(
                source_stage_id=draft.edges[0].target_stage_id,
                target_stage_id=draft.edges[0].source_stage_id,
                dependency_type=GraphDependencyType.DATA,
                artifact_id=draft.nodes[1].output_artifacts[0].artifact_id,
                evidence=("adversarial recursive edge",),
            ),
        )
    else:
        changes["edges"] = ()

    result = validate_composition_candidate(draft.model_copy(update=changes), context)

    assert result.status is CompositionValidationStatus.FAIL
    assert issue_id in {item.issue_id for item in result.issues}


def test_repeated_primary_substitution_is_rejected() -> None:
    records = (model("model-a"), model("model-b", provider="provider-b"))
    request = instantiation_request(
        topology=CertifiedTopology.PRIMARY_SPECIALIST_PRIMARY,
        records=records,
    )
    result = instantiate_composition_candidates(request)
    draft = next(
        item
        for item in result.drafts
        if item.topology is CertifiedTopology.PRIMARY_SPECIALIST_PRIMARY
    )
    nodes = list(draft.nodes)
    primary_indexes = [
        index for index, node in enumerate(nodes) if node.role is CompositionRole.PRIMARY
    ]
    nodes[primary_indexes[1]] = nodes[primary_indexes[1]].model_copy(
        update={"model_record": records[1]}
    )
    context = CompositionValidationContext(
        intelligence_result=request.intelligence_result,
        graph=request.graph,
        readiness_result=request.readiness_result,
        registry=request.registry,
        hard_requirement_ids=draft.satisfied_requirement_ids,
    )

    validated = validate_composition_candidate(
        draft.model_copy(update={"nodes": tuple(nodes)}), context
    )

    assert "repeated_primary_identity" in {
        item.issue_id for item in validated.issues
    }


@pytest.mark.parametrize(
    ("topology", "source_role", "issue_id"),
    (
        (
            CertifiedTopology.PRIMARY_VERIFIER,
            CompositionRole.PRIMARY,
            "handoff_compatibility",
        ),
        (
            CertifiedTopology.PRIMARY_SPECIALIST_PRIMARY,
            CompositionRole.SPECIALIST,
            "specialist_handoff",
        ),
        (
            CertifiedTopology.PRIMARY_RETRIEVAL_PRIMARY,
            CompositionRole.RETRIEVAL_AUGMENTER,
            "retrieval_handoff",
        ),
        (
            CertifiedTopology.PRIMARY_TOOL_PRIMARY,
            CompositionRole.TOOL_MODEL,
            "tool_handoff",
        ),
    ),
)
def test_incompatible_or_degraded_handoffs_fail_closed(
    topology: CertifiedTopology,
    source_role: CompositionRole,
    issue_id: str,
) -> None:
    draft, context = draft_and_context(topology)
    source = next(node for node in draft.nodes if node.role is source_role)
    if issue_id == "handoff_compatibility":
        replacement = artifact("primary-output", ModelModality.IMAGE)
    else:
        replacement = artifact("generic-text-output")
    changed_source = source.model_copy(update={"output_artifacts": (replacement,)})
    nodes = tuple(
        changed_source if node.stage_id == source.stage_id else node
        for node in draft.nodes
    )
    edges = tuple(
        edge.model_copy(update={"artifact_id": replacement.artifact_id})
        if edge.source_stage_id == source.stage_id
        else edge
        for edge in draft.edges
    )

    validated = validate_composition_candidate(
        draft.model_copy(update={"nodes": nodes, "edges": edges}), context
    )

    assert issue_id in {item.issue_id for item in validated.issues}


def test_structured_artifact_cannot_be_degraded_to_generic_text() -> None:
    draft, context = draft_and_context(CertifiedTopology.PRIMARY_VERIFIER)
    source = next(node for node in draft.nodes if node.role is CompositionRole.PRIMARY)
    structured = artifact(
        "structured-result", ModelModality.STRUCTURED_DATA, structured=True
    )
    changed_source = source.model_copy(update={"output_artifacts": (structured,)})
    nodes = tuple(
        changed_source if node.stage_id == source.stage_id else node
        for node in draft.nodes
    )
    edges = tuple(
        edge.model_copy(update={"artifact_id": "generic-text-output"})
        for edge in draft.edges
    )

    validated = validate_composition_candidate(
        draft.model_copy(update={"nodes": nodes, "edges": edges}), context
    )

    assert "structured_handoff" in {item.issue_id for item in validated.issues}


def test_missing_provenance_and_blank_capability_justification_are_rejected() -> None:
    draft, context = draft_and_context()
    original = draft.nodes[0].justifications[0]
    blank = CapabilityJustification.model_construct(
        requirement_id=original.requirement_id,
        capability_field=original.capability_field,
        declared_value=original.declared_value,
        reason=" ",
    )
    node = draft.nodes[0].model_copy(update={"justifications": (blank,)})

    validated = validate_composition_candidate(
        draft.model_copy(update={"nodes": (node,), "provenance": ()}), context
    )

    assert {"provenance", "capability_justification"}.issubset(
        {item.issue_id for item in validated.issues}
    )


def test_true_duplicates_merge_all_provenance_deterministically() -> None:
    draft, _ = draft_and_context()
    extra = CompositionProvenanceReference(
        source_phase="phase5",
        artifact_id="independent-source",
        evidence="independent duplicate provenance",
    )
    duplicate = draft.model_copy(update={"provenance": (*draft.provenance, extra)})

    left = merge_duplicate_drafts(draft, duplicate)
    right = merge_duplicate_drafts(duplicate, draft)

    assert left == right
    assert extra in left.provenance
    assert semantic_candidate_signature(draft) == semantic_candidate_signature(duplicate)


def test_different_exact_revisions_remain_distinct_candidates() -> None:
    request = generation_request(
        records=(model("model-a", revision="rev-1"), model("model-a", revision="rev-2"))
    )

    result = generate_compositions(request)

    assert len(result.valid_candidates) == 2
    assert {
        canonical_model_identity(candidate.nodes[0].model_record)[-1]
        for candidate in result.valid_candidates
    } == {"rev-1", "rev-2"}


def test_caller_cap_is_bounded_and_truncation_is_transparent() -> None:
    records = tuple(
        model(f"model-{index}", provider=f"provider-{index}") for index in range(3)
    )
    result = generate_compositions(
        generation_request(records=records, max_candidates=2)
    )

    assert len(result.valid_candidates) == 2
    assert result.generation_metadata.truncated is True
    assert result.generation_metadata.enumeration_complete is False
    assert result.generation_metadata.candidate_count_lower_bound == 3
    assert result.generation_metadata.truncation_reason
    with pytest.raises(ValidationError):
        CompositionGenerationPolicy(max_nodes=3, max_candidates=257)


def test_smaller_node_cap_isolates_rejected_candidates_from_valid_candidates() -> None:
    result = generate_compositions(
        generation_request(
            topology=CertifiedTopology.PRIMARY_SPECIALIST_PRIMARY,
            composition_required=False,
            max_nodes=2,
        )
    )

    assert result.status is CompositionResultStatus.READY
    assert result.valid_candidates
    assert result.rejected_candidates
    assert all(candidate.rejection_reasons for candidate in result.rejected_candidates)


def test_all_rejected_required_candidates_produce_fail() -> None:
    result = generate_compositions(
        generation_request(
            topology=CertifiedTopology.PRIMARY_SPECIALIST_PRIMARY,
            max_nodes=2,
        )
    )

    assert result.status is CompositionResultStatus.FAIL
    assert result.valid_candidates == ()
    assert result.rejected_candidates


def test_equivalent_input_permutations_produce_identical_final_result() -> None:
    records = (
        model("model-z", provider="provider-z"),
        model("model-a", provider="provider-a"),
    )
    roles = (
        role_requirement(CompositionRole.SPECIALIST),
        role_requirement(CompositionRole.CRITIC),
    )
    first = generation_request(
        topology=CertifiedTopology.PRIMARY_SPECIALIST_PRIMARY,
        records=records,
        role_requirements=roles,
    )
    second = generation_request(
        topology=CertifiedTopology.PRIMARY_SPECIALIST_PRIMARY,
        records=tuple(reversed(records)),
        role_requirements=tuple(reversed(roles)),
    )

    assert generate_compositions(first) == generate_compositions(second)


def test_full_pipeline_does_not_mutate_any_input() -> None:
    request = generation_request(
        topology=CertifiedTopology.PRIMARY_SPECIALIST_PRIMARY,
        composition_required=False,
    )
    before = request.model_dump(mode="python")

    result = generate_compositions(request)

    assert request.model_dump(mode="python") == before
    with pytest.raises(ValidationError):
        result.status = CompositionResultStatus.FAIL  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        request.instantiation_request.graph.graph_id = "changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    "field",
    (
        "rank",
        "score",
        "winner",
        "best_model",
        "preferred_candidate",
        "fallback_ordering",
        "graph_node_assignment",
        "hardware",
        "device",
        "placement",
        "scheduler_assignment",
        "runtime_invocation",
        "cost_optimization",
        "latency_optimization",
        "quality_optimization",
    ),
)
def test_nested_phase6_decision_leakage_is_rejected(field: str) -> None:
    draft, context = draft_and_context()
    changed = draft.model_copy()
    object.__setattr__(changed.nodes[0], field, {"nested": "forbidden"})

    result = validate_composition_candidate(changed, context)

    assert result.status is CompositionValidationStatus.FAIL
    assert "boundary_compliance" in {item.issue_id for item in result.issues}


def test_rejection_reasons_and_order_are_deterministic() -> None:
    draft, context = draft_and_context()
    changed = draft.model_copy(
        update={"request_id": "wrong", "provenance": (), "composition_id": "bad"}
    )

    first = validate_composition_candidate(changed, context)
    second = validate_composition_candidate(changed, context)

    assert first == second
    assert tuple(item.issue_id for item in first.issues) == tuple(
        sorted(item.issue_id for item in first.issues)
    )
    assert tuple(item.issue_id for item in first.candidate.rejection_reasons) == tuple(
        item.issue_id for item in first.issues
    )
