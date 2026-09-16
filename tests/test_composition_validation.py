from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from mercury.composition.contracts import (
    CapabilityJustification,
    CertifiedTopology,
    CompositionArtifactContract,
    CompositionCandidateDraft,
    CompositionEdge,
    CompositionRole,
    CompositionValidity,
)
from mercury.composition.instantiation import (
    CompositionEvidenceConstraint,
    CompositionInstantiationRequest,
    CompositionRoleRequirement,
    instantiate_composition_candidates,
)
from mercury.composition.patterns import get_certified_patterns
from mercury.composition.validation import (
    CompositionValidationContext,
    CompositionValidationResult,
    CompositionValidationStatus,
    validate_composition_candidate,
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
    EvidenceAssessmentStatus,
    assess_capability_evidence,
)
from mercury.models.registry import ModelCapabilityRegistry


def pipeline():
    request = WorkloadRequest(
        workload_id="workload-1", session_id="session-1", task_type="inference",
        input={"text": "hello"}, context={}, latency_target_ms=100.0,
        quality_target=0.9, cost_budget=None, privacy_level="confidential",
        priority=50, hardware_constraints=(),
    )
    identity = GatewayIdentity(request_id="request-1", workload_id="workload-1", session_id="session-1")
    envelope = GatewayRequestEnvelope(
        gateway_request_id="gateway-request-1", identity=identity,
        workload_request=request, received_at=datetime(2026, 9, 17, tzinfo=UTC),
        normalized=False, validation_status=GatewayValidationStatus.ACCEPTED,
        validation_evidence=GatewayValidationEvidence(status=GatewayValidationStatus.ACCEPTED, reasons=()),
    )
    normalization = normalize_gateway_request(envelope)
    assert normalization.normalized_request is not None
    constraints = canonicalize_gateway_constraints(identity, normalization.normalized_request)
    return analyze_workload(normalization, constraints)


def logical_graph(*extra_types: GraphNodeType) -> ExecutionGraph:
    intelligence = pipeline()
    types = (GraphNodeType.INPUT, *extra_types, GraphNodeType.REASONING, GraphNodeType.OUTPUT)
    nodes = tuple(
        ExecutionGraphNode(
            f"node-{index}", node_type, f"certified {node_type.value}",
            ({
                GraphNodeType.RETRIEVAL: ComputationalCapability.RETRIEVAL,
                GraphNodeType.TOOL: ComputationalCapability.TOOL_USE,
            }.get(node_type, ComputationalCapability.GENERATION),),
            (Evidence("phase3", "certified node"),),
        )
        for index, node_type in enumerate(types)
    )
    edges = tuple(
        ExecutionGraphEdge(
            nodes[index].node_id, nodes[index + 1].node_id,
            GraphDependencyType.DATA, (Evidence("phase3", "certified flow"),),
        )
        for index in range(len(nodes) - 1)
    )
    return ExecutionGraph(
        "graph-1", "request-1", "workload-1", "session-1", nodes, edges,
        (Evidence("phase2", "certified intelligence provenance"),),
        intelligence.profile,
    )


def ready(graph: ExecutionGraph) -> GraphReadinessResult:
    return GraphReadinessResult(
        graph.graph_id, graph.request_id, graph.workload_id, graph.session_id,
        GraphReadinessStatus.READY, (),
        (GraphReadinessEvidence("phase3", True, "certified ready graph"),),
    )


def model(
    model_id: str = "model-a", *, provider: str = "provider-a",
    revision: str = "rev-1", retrieval: bool = True, tool: bool = True,
) -> ModelCapabilityRecord:
    return ModelCapabilityRecord(
        model_id=model_id, provider=provider, family="family-a", revision=revision,
        input_modalities=(ModelModality.TEXT,), output_modalities=(ModelModality.TEXT,),
        reasoning_capabilities=(ReasoningCapability.GENERAL, ReasoningCapability.MULTI_STEP),
        supports_retrieval=retrieval, supports_tool_use=tool,
        supports_structured_tool_arguments=tool, supports_tool_result_consumption=tool,
        supports_code_understanding=tool, supports_json_output=True,
        supports_schema_constrained_output=True,
        provenance=CapabilityProvenance(
            source="phase4", source_revision="registry-v1", evidence="certified record"
        ),
    )


def artifact(artifact_id: str, modality: ModelModality = ModelModality.TEXT) -> CompositionArtifactContract:
    return CompositionArtifactContract(
        artifact_id=artifact_id, modalities=(modality,), requires_structured_output=False,
        evidence=("explicit logical artifact semantics",),
    )


def role_requirement(role: CompositionRole) -> CompositionRoleRequirement:
    return CompositionRoleRequirement(
        role=role, requirement_ids=(f"{role.value}-requirement",),
        requirements=ModelCapabilityRequirements(
            required_input_modalities=(ModelModality.TEXT,),
            required_output_modalities=(ModelModality.TEXT,),
            requires_retrieval=role is CompositionRole.SPECIALIST,
            evidence=(f"explicit {role.value} requirement",),
        ),
        input_artifacts=(artifact(f"{role.value}-input"),),
        output_artifacts=(artifact(f"{role.value}-output"),),
        provenance=(
            {"source_phase": "phase3", "artifact_id": f"{role.value}-requirement", "evidence": "explicit certified role requirement"},
        ),
    )


def evidence_constraint(state: CapabilityEvidenceState = CapabilityEvidenceState.VALID, *, include: bool = True) -> CompositionEvidenceConstraint:
    evidence = (
        CapabilityEvidence(
            capability_claim="text_generation", source="phase4-evidence",
            source_revision="v1", reference_id="evidence-1", detail="exact evidence",
            kind=CapabilityEvidenceKind.MEASURED, state=state, supports_claim=True,
        ),
    ) if include else ()
    return CompositionEvidenceConstraint(
        role=CompositionRole.PRIMARY, capability_claim="text_generation",
        assessment_requirements=CapabilityEvidenceAssessmentRequirements(
            capability_claim="text_generation", requires_evidence=True,
            requires_current_valid=True, reject_conflicts=True,
        ),
        evidence=evidence,
    )


def source_request(
    *, extra_types: tuple[GraphNodeType, ...] = (),
    role_requirements: tuple[CompositionRoleRequirement, ...] = (),
    records: tuple[ModelCapabilityRecord, ...] | None = None,
    constraints: tuple[CompositionEvidenceConstraint, ...] = (),
) -> CompositionInstantiationRequest:
    intelligence = pipeline()
    graph = logical_graph(*extra_types)
    return CompositionInstantiationRequest(
        intelligence_result=intelligence, graph=graph, readiness_result=ready(graph),
        registry=ModelCapabilityRegistry(records=records or (model(),)),
        role_requirements=role_requirements, evidence_constraints=constraints,
        composition_required=False,
    )


def draft_and_context(
    topology: CertifiedTopology = CertifiedTopology.SINGLE,
    *, evidence: CompositionEvidenceConstraint | None = None,
) -> tuple[CompositionCandidateDraft, CompositionValidationContext]:
    extras: tuple[GraphNodeType, ...] = ()
    roles: tuple[CompositionRoleRequirement, ...] = ()
    if topology is CertifiedTopology.PRIMARY_VERIFIER:
        extras = (GraphNodeType.VALIDATION,)
    elif topology is CertifiedTopology.PRIMARY_CRITIC:
        roles = (role_requirement(CompositionRole.CRITIC),)
    elif topology is CertifiedTopology.PRIMARY_SPECIALIST_PRIMARY:
        roles = (role_requirement(CompositionRole.SPECIALIST),)
    elif topology is CertifiedTopology.PRIMARY_RETRIEVAL_PRIMARY:
        extras = (GraphNodeType.RETRIEVAL,)
    elif topology is CertifiedTopology.PRIMARY_TOOL_PRIMARY:
        extras = (GraphNodeType.TOOL,)
    elif topology is CertifiedTopology.PRIMARY_SPECIALIST_VERIFIER:
        extras = (GraphNodeType.VALIDATION,)
        roles = (role_requirement(CompositionRole.SPECIALIST),)
    request = source_request(
        extra_types=extras, role_requirements=roles,
        constraints=((evidence,) if evidence is not None else ()),
    )
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


def validate_mutation(
    draft: CompositionCandidateDraft,
    context: CompositionValidationContext,
    **changes: object,
) -> CompositionValidationResult:
    return validate_composition_candidate(draft.model_copy(update=changes), context)


@pytest.mark.parametrize("topology", tuple(CertifiedTopology))
def test_every_certified_topology_validates_independently(topology: CertifiedTopology) -> None:
    draft, context = draft_and_context(topology)

    result = validate_composition_candidate(draft, context)

    assert result.status is CompositionValidationStatus.PASS
    assert result.candidate.validity is CompositionValidity.VALID
    assert result.candidate.rejection_reasons == ()


def test_validation_is_deterministic_and_does_not_mutate_draft() -> None:
    draft, context = draft_and_context(CertifiedTopology.PRIMARY_VERIFIER)
    before = draft.model_dump(mode="python")

    first = validate_composition_candidate(draft, context)
    second = validate_composition_candidate(draft, context)

    assert first == second
    assert draft.model_dump(mode="python") == before
    with pytest.raises(ValidationError):
        first.status = CompositionValidationStatus.FAIL  # type: ignore[misc]


@pytest.mark.parametrize(
    ("changes", "issue_id"),
    (
        ({"schema_version": "mercury.model-composition/v2"}, "schema_version"),
        ({"request_id": "other-request"}, "identity_consistency"),
        ({"pattern_id": "pattern-primary-critic-v1"}, "pattern_conformance"),
        ({"composition_id": "sha256:" + "0" * 64}, "composition_id"),
    ),
)
def test_schema_identity_pattern_and_stale_id_fail_closed(
    changes: dict[str, object], issue_id: str
) -> None:
    draft, context = draft_and_context()

    result = validate_mutation(draft, context, **changes)

    assert result.status is CompositionValidationStatus.FAIL
    assert issue_id in {item.issue_id for item in result.issues}


def test_exact_registry_revision_mismatch_is_rejected() -> None:
    draft, context = draft_and_context()
    wrong = model(revision="rev-2")
    changed_node = draft.nodes[0].model_copy(update={"model_record": wrong})

    result = validate_mutation(draft, context, nodes=(changed_node,))

    assert "registry_identity" in {item.issue_id for item in result.issues}
    assert changed_node.model_record.revision == "rev-2"


def test_unknown_role_is_rejected_without_repair() -> None:
    draft, context = draft_and_context()
    changed = draft.nodes[0].model_copy(update={"role": "router"})

    result = validate_mutation(draft, context, nodes=(changed,))

    assert result.status is CompositionValidationStatus.FAIL
    assert "certified_role" in {item.issue_id for item in result.issues}
    assert result.candidate.nodes[0].role == "router"


@pytest.mark.parametrize("defect", ("duplicate", "dangling", "self", "cycle", "orphan"))
def test_malformed_graph_structure_is_rejected_without_repair(defect: str) -> None:
    draft, context = draft_and_context(CertifiedTopology.PRIMARY_VERIFIER)
    nodes = draft.nodes
    edges = draft.edges
    if defect == "duplicate":
        nodes = (nodes[0], nodes[0])
    elif defect == "dangling":
        edges = (edges[0].model_copy(update={"target_stage_id": "missing"}),)
    elif defect == "self":
        edges = (edges[0].model_copy(update={"target_stage_id": edges[0].source_stage_id}),)
    elif defect == "cycle":
        edges = (*edges, CompositionEdge.model_construct(
            source_stage_id=edges[0].target_stage_id,
            target_stage_id=edges[0].source_stage_id,
            dependency_type=GraphDependencyType.DATA,
            artifact_id=nodes[1].output_artifacts[0].artifact_id,
            evidence=("adversarial backward flow",),
        ))
    else:
        edges = ()

    result = validate_mutation(draft, context, nodes=nodes, edges=edges)

    assert result.status is CompositionValidationStatus.FAIL
    assert result.candidate.model_dump(mode="python")["edges"] == tuple(
        item.model_dump(mode="python") for item in edges
    )


def test_repeated_primary_exact_identity_is_required() -> None:
    request = source_request(
        role_requirements=(role_requirement(CompositionRole.SPECIALIST),),
        records=(model("model-a"), model("model-b", provider="provider-b")),
    )
    result = instantiate_composition_candidates(request)
    draft = next(item for item in result.drafts if item.topology is CertifiedTopology.PRIMARY_SPECIALIST_PRIMARY)
    nodes = list(draft.nodes)
    primary_indexes = [index for index, item in enumerate(nodes) if item.role is CompositionRole.PRIMARY]
    nodes[primary_indexes[1]] = nodes[primary_indexes[1]].model_copy(
        update={"model_record": request.registry.records[1]}
    )
    context = CompositionValidationContext(
        intelligence_result=request.intelligence_result, graph=request.graph,
        readiness_result=request.readiness_result, registry=request.registry,
        hard_requirement_ids=draft.satisfied_requirement_ids,
    )

    validated = validate_mutation(draft, context, nodes=tuple(nodes))

    assert "repeated_primary_identity" in {item.issue_id for item in validated.issues}


def test_missing_capability_and_modality_are_rejected_by_phase4_compatibility() -> None:
    draft, context = draft_and_context()
    requirements = draft.nodes[0].requirements.model_copy(
        update={"requires_retrieval": True, "required_input_modalities": (ModelModality.IMAGE,)}
    )
    changed = draft.nodes[0].model_copy(update={"requirements": requirements})

    result = validate_mutation(draft, context, nodes=(changed,))

    assert "capability_compatibility" in {item.issue_id for item in result.issues}


def test_incomplete_hard_requirement_coverage_is_rejected() -> None:
    draft, context = draft_and_context()
    incomplete = context.model_copy(update={"hard_requirement_ids": ("missing-hard-requirement",)})

    result = validate_composition_candidate(draft, incomplete)

    assert "requirement_coverage" in {item.issue_id for item in result.issues}


def test_incompatible_handoff_modalities_are_rejected() -> None:
    draft, context = draft_and_context(CertifiedTopology.PRIMARY_VERIFIER)
    source = next(item for item in draft.nodes if item.role is CompositionRole.PRIMARY)
    changed_source = source.model_copy(update={"output_artifacts": (artifact("primary-output", ModelModality.IMAGE),)})
    nodes = tuple(changed_source if item.stage_id == source.stage_id else item for item in draft.nodes)

    result = validate_mutation(draft, context, nodes=nodes)

    assert "handoff_compatibility" in {item.issue_id for item in result.issues}


@pytest.mark.parametrize(
    ("topology", "role", "semantic_issue"),
    (
        (CertifiedTopology.PRIMARY_RETRIEVAL_PRIMARY, CompositionRole.RETRIEVAL_AUGMENTER, "retrieval_handoff"),
        (CertifiedTopology.PRIMARY_TOOL_PRIMARY, CompositionRole.TOOL_MODEL, "tool_handoff"),
        (CertifiedTopology.PRIMARY_SPECIALIST_PRIMARY, CompositionRole.SPECIALIST, "specialist_handoff"),
    ),
)
def test_specialized_artifact_cannot_be_replaced_by_generic_text(
    topology: CertifiedTopology, role: CompositionRole, semantic_issue: str
) -> None:
    draft, context = draft_and_context(topology)
    source = next(item for item in draft.nodes if item.role is role)
    generic = artifact("generic-text-output")
    changed_source = source.model_copy(update={"output_artifacts": (generic,)})
    nodes = tuple(changed_source if item.stage_id == source.stage_id else item for item in draft.nodes)
    edges = tuple(
        item.model_copy(update={"artifact_id": generic.artifact_id})
        if item.source_stage_id == source.stage_id else item
        for item in draft.edges
    )

    result = validate_mutation(draft, context, nodes=nodes, edges=edges)

    assert semantic_issue in {item.issue_id for item in result.issues}


def test_generic_text_cannot_replace_structured_handoff() -> None:
    draft, context = draft_and_context(CertifiedTopology.PRIMARY_VERIFIER)
    source = next(item for item in draft.nodes if item.role is CompositionRole.PRIMARY)
    structured = CompositionArtifactContract(
        artifact_id="structured-result", modalities=(ModelModality.STRUCTURED_DATA,),
        requires_structured_output=True, evidence=("explicit schema output",),
    )
    changed_source = source.model_copy(update={"output_artifacts": (structured,)})
    nodes = tuple(changed_source if item.stage_id == source.stage_id else item for item in draft.nodes)
    edges = tuple(item.model_copy(update={"artifact_id": "generic-text-output"}) for item in draft.edges)

    result = validate_mutation(draft, context, nodes=nodes, edges=edges)

    assert "structured_handoff" in {item.issue_id for item in result.issues}


@pytest.mark.parametrize(
    ("state", "expected_status"),
    (
        (CapabilityEvidenceState.STALE, EvidenceAssessmentStatus.STALE),
        (CapabilityEvidenceState.CONFLICTING, EvidenceAssessmentStatus.CONFLICTING),
    ),
)
def test_unacceptable_required_evidence_is_rejected(
    state: CapabilityEvidenceState, expected_status: EvidenceAssessmentStatus
) -> None:
    draft, context = draft_and_context()
    constraint = evidence_constraint(state)
    assessment = assess_capability_evidence(constraint.evidence, constraint.assessment_requirements)
    assert assessment.status is expected_status

    result = validate_mutation(draft, context, evidence_assessments=(assessment,))

    assert "required_evidence" in {item.issue_id for item in result.issues}


def test_missing_required_evidence_rejected_but_acceptable_evidence_passes() -> None:
    draft, context = draft_and_context()
    missing = evidence_constraint(include=False)
    insufficient = assess_capability_evidence(missing.evidence, missing.assessment_requirements)
    failed = validate_mutation(draft, context, evidence_assessments=(insufficient,))
    assert "required_evidence" in {item.issue_id for item in failed.issues}

    acceptable = evidence_constraint()
    assessment = assess_capability_evidence(acceptable.evidence, acceptable.assessment_requirements)
    passed = validate_mutation(draft, context, evidence_assessments=(assessment,))
    assert passed.status is CompositionValidationStatus.PASS


def test_missing_provenance_and_blank_justification_are_rejected() -> None:
    draft, context = draft_and_context()
    justification = draft.nodes[0].justifications[0].model_copy(update={"reason": " "})
    changed_node = draft.nodes[0].model_copy(update={"justifications": (justification,)})

    result = validate_mutation(draft, context, nodes=(changed_node,), provenance=())

    assert {"provenance", "capability_justification"}.issubset(
        {item.issue_id for item in result.issues}
    )


@pytest.mark.parametrize(
    "field",
    (
        "rank", "score", "winner", "preferred_candidate", "selected_model",
        "fallback_ordering", "graph_node_assignment", "cost_optimization",
        "latency_optimization", "quality_optimization", "hardware", "placement",
        "scheduler_assignment", "runtime_invocation",
    ),
)
def test_nested_boundary_leakage_is_rejected(field: str) -> None:
    draft, context = draft_and_context()
    changed = draft.model_copy()
    object.__setattr__(changed.nodes[0], field, {"nested": "leak"})

    result = validate_composition_candidate(changed, context)

    assert "boundary_compliance" in {item.issue_id for item in result.issues}


def test_issue_ordering_is_deterministic_and_candidate_reasons_match() -> None:
    draft, context = draft_and_context()
    changed = draft.model_copy(update={"request_id": "other", "provenance": (), "composition_id": "bad"})

    first = validate_composition_candidate(changed, context)
    second = validate_composition_candidate(changed, context)

    assert first == second
    assert tuple(item.issue_id for item in first.issues) == tuple(
        sorted(item.issue_id for item in first.issues)
    )
    assert tuple(item.issue_id for item in first.candidate.rejection_reasons) == tuple(
        item.issue_id for item in first.issues
    )


def test_one_rejected_candidate_does_not_affect_another() -> None:
    draft, context = draft_and_context()
    rejected = validate_mutation(draft, context, request_id="other")
    valid = validate_composition_candidate(draft, context)

    assert rejected.status is CompositionValidationStatus.FAIL
    assert valid.status is CompositionValidationStatus.PASS
    assert valid.candidate.rejection_reasons == ()


def test_checked_invariants_and_collections_are_immutable() -> None:
    draft, context = draft_and_context()
    result = validate_composition_candidate(draft, context)

    assert isinstance(result.checked_invariant_ids, tuple)
    assert "boundary_compliance" in result.checked_invariant_ids
    with pytest.raises(TypeError):
        result.checked_invariant_ids[0] = "changed"  # type: ignore[index]
