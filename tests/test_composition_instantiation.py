from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from mercury.composition.contracts import (
    CertifiedTopology,
    CompositionArtifactContract,
    CompositionRole,
    canonical_model_identity,
)
from mercury.composition.instantiation import (
    CompositionEvidenceConstraint,
    CompositionInstantiationRequest,
    CompositionInstantiationResult,
    CompositionRoleRequirement,
    InstantiationIssue,
    derive_role_requirements,
    instantiate_composition_candidates,
    iter_composition_candidate_drafts,
)
from mercury.composition.patterns import get_certified_pattern, get_certified_patterns
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
    EvidenceAssessmentStatus,
)
from mercury.models.registry import ModelCapabilityRegistry


def intelligence():
    request = WorkloadRequest(
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
        workload_request=request,
        received_at=datetime(2026, 9, 17, tzinfo=UTC),
        normalized=False,
        validation_status=GatewayValidationStatus.ACCEPTED,
        validation_evidence=GatewayValidationEvidence(
            status=GatewayValidationStatus.ACCEPTED, reasons=()
        ),
    )
    normalization = normalize_gateway_request(envelope)
    assert normalization.normalized_request is not None
    constraints = canonicalize_gateway_constraints(
        identity, normalization.normalized_request
    )
    result = analyze_workload(normalization, constraints)
    assert result.status is not PipelineStatus.FAIL
    return result


def graph(*extra_types: GraphNodeType) -> ExecutionGraph:
    pipeline = intelligence()
    node_types = (GraphNodeType.INPUT, *extra_types, GraphNodeType.REASONING, GraphNodeType.OUTPUT)
    nodes = []
    for index, node_type in enumerate(node_types):
        capability = {
            GraphNodeType.RETRIEVAL: ComputationalCapability.RETRIEVAL,
            GraphNodeType.TOOL: ComputationalCapability.TOOL_USE,
        }.get(node_type, ComputationalCapability.GENERATION)
        nodes.append(
            ExecutionGraphNode(
                node_id=f"node-{index}",
                node_type=node_type,
                purpose=f"certified {node_type.value} stage",
                required_capabilities=(capability,),
                evidence=(Evidence("phase3", "certified logical stage"),),
            )
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
        nodes=tuple(nodes),
        edges=edges,
        provenance=(Evidence("phase2", "certified workload intelligence"),),
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


def record(
    model_id: str = "model-a",
    *,
    provider: str = "provider-a",
    revision: str = "rev-1",
    retrieval: bool = False,
    tool: bool = False,
    modalities: tuple[ModelModality, ...] = (ModelModality.TEXT,),
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


def artifact(artifact_id: str) -> CompositionArtifactContract:
    return CompositionArtifactContract(
        artifact_id=artifact_id,
        modalities=(ModelModality.TEXT,),
        requires_structured_output=False,
        evidence=("certified logical artifact",),
    )


def role_requirement(
    role: CompositionRole,
    *,
    requires_retrieval: bool = False,
) -> CompositionRoleRequirement:
    return CompositionRoleRequirement(
        role=role,
        requirement_ids=(f"{role.value}-requirement",),
        requirements=ModelCapabilityRequirements(
            required_input_modalities=(ModelModality.TEXT,),
            required_output_modalities=(ModelModality.TEXT,),
            requires_retrieval=requires_retrieval,
            evidence=(f"explicit {role.value} requirement",),
        ),
        input_artifacts=(artifact(f"{role.value}-input"),),
        output_artifacts=(artifact(f"{role.value}-output"),),
        provenance=(
            {
                "source_phase": "phase3",
                "artifact_id": f"{role.value}-logical-requirement",
                "evidence": f"certified explicit {role.value} requirement",
            },
        ),
    )


def evidence_constraint(
    *, required: bool, include_evidence: bool
) -> CompositionEvidenceConstraint:
    evidence = (
        CapabilityEvidence(
            capability_claim="text_generation",
            source="phase4-evidence",
            source_revision="evidence-v1",
            reference_id="evidence-1",
            detail="measured support for text generation",
            kind=CapabilityEvidenceKind.MEASURED,
            state=CapabilityEvidenceState.VALID,
            supports_claim=True,
        ),
    ) if include_evidence else ()
    return CompositionEvidenceConstraint(
        role=CompositionRole.PRIMARY,
        capability_claim="text_generation",
        assessment_requirements=CapabilityEvidenceAssessmentRequirements(
            capability_claim="text_generation",
            requires_evidence=required,
            requires_current_valid=required,
        ),
        evidence=evidence,
    )


def instantiation_request(
    *,
    records: tuple[ModelCapabilityRecord, ...] | None = None,
    extra_types: tuple[GraphNodeType, ...] = (),
    role_requirements: tuple[CompositionRoleRequirement, ...] = (),
    evidence_constraints: tuple[CompositionEvidenceConstraint, ...] = (),
    composition_required: bool = False,
) -> CompositionInstantiationRequest:
    pipeline = intelligence()
    source_graph = graph(*extra_types)
    return CompositionInstantiationRequest(
        intelligence_result=pipeline,
        graph=source_graph,
        readiness_result=readiness(source_graph),
        registry=ModelCapabilityRegistry(
            records=records if records is not None else (record(),)
        ),
        role_requirements=role_requirements,
        evidence_constraints=evidence_constraints,
        composition_required=composition_required,
    )


def test_single_produces_one_deterministic_draft_with_exact_identity() -> None:
    request = instantiation_request()

    first = instantiate_composition_candidates(request)
    second = instantiate_composition_candidates(request)

    assert first == second
    assert len(first.drafts) == 1
    assert first.drafts[0].topology is CertifiedTopology.SINGLE
    assert first.drafts[0].composition_id.startswith("sha256:")
    assert first.drafts[0].nodes[0].model_record is request.registry.records[0]
    assert canonical_model_identity(first.drafts[0].nodes[0].model_record) == (
        "provider-a", "family-a", "model-a", "rev-1"
    )


def test_zero_compatible_records_produces_zero_drafts_without_phase5_failure() -> None:
    request = instantiation_request(
        records=(record(modalities=(ModelModality.IMAGE,)),)
    )

    result = instantiate_composition_candidates(request)

    assert result.drafts == ()
    assert all(issue.reason.strip() for issue in result.issues)


def test_multiple_records_produce_canonical_many_drafts_without_provider_preference() -> None:
    request = instantiation_request(
        records=(
            record("model-z", provider="provider-z"),
            record("model-a", provider="provider-a"),
        )
    )

    result = instantiate_composition_candidates(request)

    assert tuple(
        canonical_model_identity(item.nodes[0].model_record) for item in result.drafts
    ) == (
        ("provider-a", "family-a", "model-a", "rev-1"),
        ("provider-z", "family-a", "model-z", "rev-1"),
    )
    assert tuple(iter_composition_candidate_drafts(request)) == result.drafts


def test_equivalent_registry_input_produces_same_ids_and_order() -> None:
    records = (
        record("model-z", provider="provider-z"),
        record("model-a", provider="provider-a"),
    )
    first = instantiate_composition_candidates(instantiation_request(records=records))
    second = instantiate_composition_candidates(
        instantiation_request(records=tuple(reversed(records)))
    )

    assert tuple(item.composition_id for item in first.drafts) == tuple(
        item.composition_id for item in second.drafts
    )


@pytest.mark.parametrize(
    ("topology", "extra_types", "requirements"),
    (
        (CertifiedTopology.PRIMARY_VERIFIER, (GraphNodeType.VALIDATION,), ()),
        (
            CertifiedTopology.PRIMARY_CRITIC,
            (),
            (role_requirement(CompositionRole.CRITIC),),
        ),
        (
            CertifiedTopology.PRIMARY_SPECIALIST_PRIMARY,
            (),
            (role_requirement(CompositionRole.SPECIALIST),),
        ),
        (
            CertifiedTopology.PRIMARY_RETRIEVAL_PRIMARY,
            (GraphNodeType.RETRIEVAL,),
            (),
        ),
        (
            CertifiedTopology.PRIMARY_TOOL_PRIMARY,
            (GraphNodeType.TOOL,),
            (),
        ),
        (
            CertifiedTopology.PRIMARY_SPECIALIST_VERIFIER,
            (GraphNodeType.VALIDATION,),
            (role_requirement(CompositionRole.SPECIALIST),),
        ),
    ),
)
def test_specialized_pattern_is_instantiated_only_by_explicit_certified_state(
    topology: CertifiedTopology,
    extra_types: tuple[GraphNodeType, ...],
    requirements: tuple[CompositionRoleRequirement, ...],
) -> None:
    request = instantiation_request(
        records=(record(retrieval=True, tool=True),),
        extra_types=extra_types,
        role_requirements=requirements,
    )

    result = instantiate_composition_candidates(request)

    assert topology in result.applicable_topologies
    assert any(item.topology is topology for item in result.drafts)


def test_inapplicable_patterns_do_not_increase_candidate_count() -> None:
    result = instantiate_composition_candidates(instantiation_request())

    assert result.applicable_topologies == (CertifiedTopology.SINGLE,)
    assert tuple(item.topology for item in result.drafts) == (CertifiedTopology.SINGLE,)


def test_repeated_primary_binding_never_substitutes_an_alternative_identity() -> None:
    request = instantiation_request(
        records=(
            record("primary-a"),
            record("primary-b", provider="provider-b"),
            record("specialist", provider="provider-s", retrieval=True),
        ),
        role_requirements=(
            role_requirement(CompositionRole.SPECIALIST, requires_retrieval=True),
        ),
    )

    result = instantiate_composition_candidates(request)
    drafts = tuple(
        item
        for item in result.drafts
        if item.topology is CertifiedTopology.PRIMARY_SPECIALIST_PRIMARY
    )

    assert drafts
    for value in drafts:
        primary_nodes = tuple(
            item for item in value.nodes if item.role is CompositionRole.PRIMARY
        )
        assert len(primary_nodes) == 2
        assert canonical_model_identity(primary_nodes[0].model_record) == (
            canonical_model_identity(primary_nodes[1].model_record)
        )


def test_incompatible_record_and_model_name_keywords_cannot_create_binding() -> None:
    result = instantiate_composition_candidates(
        instantiation_request(
            records=(
                record(
                    "best-text-generation-model",
                    provider="preferred-provider",
                    modalities=(ModelModality.IMAGE,),
                ),
            )
        )
    )

    assert result.drafts == ()


def test_missing_required_evidence_blocks_binding_and_preserves_assessment() -> None:
    request = instantiation_request(
        evidence_constraints=(
            evidence_constraint(required=True, include_evidence=False),
        )
    )

    result = instantiate_composition_candidates(request)

    assert result.drafts == ()
    assert result.evidence_assessments[0].status is EvidenceAssessmentStatus.INSUFFICIENT


def test_acceptable_required_evidence_permits_binding() -> None:
    request = instantiation_request(
        evidence_constraints=(
            evidence_constraint(required=True, include_evidence=True),
        )
    )

    result = instantiate_composition_candidates(request)

    assert result.drafts
    assert result.drafts[0].evidence_assessments[0].status is EvidenceAssessmentStatus.ACCEPTABLE


def test_absent_evidence_requirement_does_not_invent_assessment() -> None:
    result = instantiate_composition_candidates(instantiation_request())

    assert result.evidence_assessments == ()
    assert result.drafts[0].evidence_assessments == ()


def test_draft_preserves_workload_graph_registry_pattern_and_reason_provenance() -> None:
    request = instantiation_request()
    value = instantiate_composition_candidates(request).drafts[0]
    artifact_ids = {item.artifact_id for item in value.provenance}

    assert {"request-1", "graph-1", request.registry.fingerprint}.issubset(artifact_ids)
    assert value.pattern_id == "pattern-single-v1"
    assert all(item.evidence.strip() for item in value.provenance)


def test_role_requirement_derivation_is_stable_and_pattern_specific() -> None:
    request = instantiation_request()
    requirements = derive_role_requirements(
        request, get_certified_pattern(CertifiedTopology.SINGLE)
    )

    assert tuple(item.role for item in requirements) == (CompositionRole.PRIMARY,)
    assert requirements[0].requirement_ids
    assert requirements[0].provenance


def test_upstream_fail_blocked_or_identity_mismatch_fails_closed() -> None:
    valid = instantiation_request()
    with pytest.raises(ValidationError):
        CompositionInstantiationRequest(
            **{
                **valid.model_dump(),
                "readiness_result": GraphReadinessResult(
                    graph_id="graph-1",
                    request_id="request-1",
                    workload_id="workload-1",
                    session_id="session-1",
                    status=GraphReadinessStatus.BLOCKED,
                    issues=(),
                    evidence=valid.readiness_result.evidence,
                ),
            }
        )
    with pytest.raises(ValidationError):
        CompositionInstantiationRequest(
            **{
                **valid.model_dump(),
                "readiness_result": GraphReadinessResult(
                    graph_id="other-graph",
                    request_id="request-1",
                    workload_id="workload-1",
                    session_id="session-1",
                    status=GraphReadinessStatus.READY,
                    issues=(),
                    evidence=valid.readiness_result.evidence,
                ),
            }
        )


def test_source_inputs_patterns_and_result_are_immutable() -> None:
    request = instantiation_request()
    patterns_before = get_certified_patterns()
    registry_before = request.registry
    result = instantiate_composition_candidates(request)

    assert request.registry == registry_before
    assert get_certified_patterns() == patterns_before
    assert isinstance(result.drafts, tuple)
    with pytest.raises(ValidationError):
        result.drafts = ()  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        request.graph.graph_id = "changed"  # type: ignore[misc]


def test_instantiation_contracts_expose_no_ranking_or_execution_decisions() -> None:
    forbidden = {
        "rank", "score", "winner", "selected_model", "preferred_provider",
        "cost", "latency", "quality", "hardware", "device", "placement",
        "scheduler", "runtime", "graph_node_assignment",
    }
    for contract_type in (
        CompositionRoleRequirement,
        CompositionEvidenceConstraint,
        CompositionInstantiationRequest,
        InstantiationIssue,
        CompositionInstantiationResult,
    ):
        assert forbidden.isdisjoint(contract_type.model_fields)
