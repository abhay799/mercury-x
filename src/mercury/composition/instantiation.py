"""Deterministic instantiation of model-composition candidate drafts."""

from __future__ import annotations

from hashlib import sha256
from itertools import product
from json import dumps
from typing import Final, Iterator

from pydantic import field_validator, model_validator

from mercury.composition.contracts import (
    COMPOSITION_SCHEMA_VERSION,
    CapabilityJustification,
    CertifiedTopology,
    CompositionArtifactContract,
    CompositionCandidateDraft,
    CompositionEdge,
    CompositionNode,
    CompositionProvenanceReference,
    CompositionRole,
)
from mercury.composition.patterns import (
    CertifiedCompositionPattern,
    get_certified_patterns,
)
from mercury.contracts.base import ContractModel
from mercury.graph.models import ExecutionGraph, GraphNodeType
from mercury.graph.readiness import GraphReadinessResult, GraphReadinessStatus
from mercury.intelligence.models import (
    ComputationalCapability,
    ReasoningComplexity,
    WorkloadModality,
)
from mercury.intelligence.pipeline import PipelineStatus, WorkloadIntelligencePipelineResult
from mercury.models.capabilities import (
    ModelCapabilityRecord,
    ModelModality,
    ReasoningCapability,
)
from mercury.models.compatibility import ModelCapabilityRequirements
from mercury.models.discovery import CapabilityDiscoveryQuery, discover_capabilities
from mercury.models.evidence import (
    CapabilityEvidence,
    CapabilityEvidenceAssessment,
    CapabilityEvidenceAssessmentRequirements,
    EvidenceAssessmentStatus,
    assess_capability_evidence,
)
from mercury.models.registry import ModelCapabilityRegistry


def _nonblank(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be nonblank")
    return value


def _provenance_key(
    item: CompositionProvenanceReference,
) -> tuple[str, str, str]:
    return item.source_phase, item.artifact_id, item.evidence


class CompositionRoleRequirement(ContractModel):
    role: CompositionRole
    requirement_ids: tuple[str, ...]
    requirements: ModelCapabilityRequirements
    input_artifacts: tuple[CompositionArtifactContract, ...]
    output_artifacts: tuple[CompositionArtifactContract, ...]
    provenance: tuple[CompositionProvenanceReference, ...]

    @field_validator("requirement_ids", mode="after")
    @classmethod
    def requirement_ids_are_canonical(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if any(not isinstance(item, str) or not item.strip() for item in values):
            raise ValueError("requirement_ids must contain nonblank values")
        normalized = tuple(sorted(set(values)))
        if not normalized:
            raise ValueError("requirement_ids must not be empty")
        return normalized

    @field_validator("input_artifacts", "output_artifacts", mode="after")
    @classmethod
    def artifacts_are_canonical(
        cls, values: tuple[CompositionArtifactContract, ...]
    ) -> tuple[CompositionArtifactContract, ...]:
        if any(not isinstance(item, CompositionArtifactContract) for item in values):
            raise ValueError("artifacts must contain CompositionArtifactContract values")
        by_id = {item.artifact_id: item for item in values}
        if len(by_id) != len(values):
            raise ValueError("artifact ids must be unique")
        normalized = tuple(by_id[key] for key in sorted(by_id))
        if not normalized:
            raise ValueError("role artifacts must not be empty")
        return normalized

    @field_validator("provenance", mode="after")
    @classmethod
    def provenance_is_canonical(
        cls, values: tuple[CompositionProvenanceReference, ...]
    ) -> tuple[CompositionProvenanceReference, ...]:
        if any(not isinstance(item, CompositionProvenanceReference) for item in values):
            raise ValueError("provenance must contain CompositionProvenanceReference values")
        normalized = tuple(sorted({_provenance_key(item): item for item in values}.values(), key=_provenance_key))
        if not normalized:
            raise ValueError("role requirement provenance must not be empty")
        return normalized


class CompositionEvidenceConstraint(ContractModel):
    role: CompositionRole
    capability_claim: str
    assessment_requirements: CapabilityEvidenceAssessmentRequirements
    evidence: tuple[CapabilityEvidence, ...] = ()

    @field_validator("capability_claim")
    @classmethod
    def claim_is_nonblank(cls, value: str) -> str:
        return _nonblank(value, "capability_claim")

    @field_validator("evidence", mode="after")
    @classmethod
    def evidence_is_canonical(
        cls, values: tuple[CapabilityEvidence, ...]
    ) -> tuple[CapabilityEvidence, ...]:
        if any(not isinstance(item, CapabilityEvidence) for item in values):
            raise ValueError("evidence must contain CapabilityEvidence values")
        key = lambda item: (
            item.capability_claim,
            item.source,
            item.source_revision,
            item.reference_id,
            item.kind.value,
            item.state.value,
            item.supports_claim,
            item.detail,
        )
        return tuple(sorted({key(item): item for item in values}.values(), key=key))

    @model_validator(mode="after")
    def claims_are_exact(self) -> CompositionEvidenceConstraint:
        if self.assessment_requirements.capability_claim != self.capability_claim:
            raise ValueError("assessment requirement claim must match capability_claim")
        if any(item.capability_claim != self.capability_claim for item in self.evidence):
            raise ValueError("evidence claims must match capability_claim")
        return self


class CompositionInstantiationRequest(ContractModel):
    intelligence_result: WorkloadIntelligencePipelineResult
    graph: ExecutionGraph
    readiness_result: GraphReadinessResult
    registry: ModelCapabilityRegistry
    role_requirements: tuple[CompositionRoleRequirement, ...] = ()
    evidence_constraints: tuple[CompositionEvidenceConstraint, ...] = ()
    composition_required: bool = False

    @field_validator("role_requirements", mode="after")
    @classmethod
    def role_requirements_are_canonical(
        cls, values: tuple[CompositionRoleRequirement, ...]
    ) -> tuple[CompositionRoleRequirement, ...]:
        if any(not isinstance(item, CompositionRoleRequirement) for item in values):
            raise ValueError("role_requirements must contain CompositionRoleRequirement values")
        roles = tuple(item.role for item in values)
        if len(roles) != len(set(roles)):
            raise ValueError("explicit role requirements must have unique roles")
        return tuple(sorted(values, key=lambda item: item.role.value))

    @field_validator("evidence_constraints", mode="after")
    @classmethod
    def evidence_constraints_are_canonical(
        cls, values: tuple[CompositionEvidenceConstraint, ...]
    ) -> tuple[CompositionEvidenceConstraint, ...]:
        if any(not isinstance(item, CompositionEvidenceConstraint) for item in values):
            raise ValueError("evidence_constraints must contain CompositionEvidenceConstraint values")
        keys = tuple((item.role, item.capability_claim) for item in values)
        if len(keys) != len(set(keys)):
            raise ValueError("evidence constraints must be unique by role and claim")
        return tuple(sorted(values, key=lambda item: (item.role.value, item.capability_claim)))

    @model_validator(mode="after")
    def upstream_state_is_certified(self) -> CompositionInstantiationRequest:
        if not isinstance(self.intelligence_result, WorkloadIntelligencePipelineResult):
            raise ValueError("intelligence_result must use the Phase 2 pipeline contract")
        if self.intelligence_result.status is PipelineStatus.FAIL:
            raise ValueError("failed workload intelligence cannot be instantiated")
        if (
            self.intelligence_result.profile is None
            or self.intelligence_result.signals is None
            or self.intelligence_result.calibration is None
        ):
            raise ValueError("workload intelligence stages must be complete")
        if not isinstance(self.graph, ExecutionGraph):
            raise ValueError("graph must use the Phase 3 ExecutionGraph contract")
        if not self.graph.provenance:
            raise ValueError("graph provenance must not be empty")
        if self.graph.intelligence_profile is None:
            raise ValueError("graph must retain its workload intelligence profile")
        if self.readiness_result.status is not GraphReadinessStatus.READY:
            raise ValueError("graph readiness must be READY")

        identity = (
            self.intelligence_result.request_id,
            self.intelligence_result.workload_id,
            self.intelligence_result.session_id,
        )
        graph_identity = (self.graph.request_id, self.graph.workload_id, self.graph.session_id)
        readiness_identity = (
            self.readiness_result.request_id,
            self.readiness_result.workload_id,
            self.readiness_result.session_id,
        )
        if graph_identity != identity or readiness_identity != identity:
            raise ValueError("Phase 2 and Phase 3 identities must match exactly")
        if self.readiness_result.graph_id != self.graph.graph_id:
            raise ValueError("readiness graph identity must match the source graph")
        if self.graph.intelligence_profile != self.intelligence_result.profile:
            raise ValueError("graph must preserve the certified workload intelligence profile")
        return self


class InstantiationIssue(ContractModel):
    issue_id: str
    role: CompositionRole | None = None
    topology: CertifiedTopology | None = None
    reason: str

    @field_validator("issue_id", "reason")
    @classmethod
    def values_are_nonblank(cls, value: str) -> str:
        return _nonblank(value, "instantiation issue value")


class CompositionInstantiationResult(ContractModel):
    drafts: tuple[CompositionCandidateDraft, ...]
    applicable_topologies: tuple[CertifiedTopology, ...]
    evidence_assessments: tuple[CapabilityEvidenceAssessment, ...]
    issues: tuple[InstantiationIssue, ...]

    @field_validator("drafts", mode="after")
    @classmethod
    def drafts_are_validated(
        cls, values: tuple[CompositionCandidateDraft, ...]
    ) -> tuple[CompositionCandidateDraft, ...]:
        if any(type(item) is not CompositionCandidateDraft for item in values):
            raise ValueError("drafts must contain CompositionCandidateDraft values")
        ids = tuple(item.composition_id for item in values)
        if len(ids) != len(set(ids)):
            raise ValueError("instantiated draft ids must be unique")
        return values

    @field_validator("applicable_topologies", mode="after")
    @classmethod
    def topologies_follow_certified_order(
        cls, values: tuple[CertifiedTopology, ...]
    ) -> tuple[CertifiedTopology, ...]:
        if any(not isinstance(item, CertifiedTopology) for item in values):
            raise ValueError("applicable_topologies must contain CertifiedTopology values")
        if len(values) != len(set(values)):
            raise ValueError("applicable topologies must be unique")
        order = {item: index for index, item in enumerate(CertifiedTopology)}
        return tuple(sorted(values, key=order.__getitem__))

    @field_validator("evidence_assessments", mode="after")
    @classmethod
    def assessments_are_canonical(
        cls, values: tuple[CapabilityEvidenceAssessment, ...]
    ) -> tuple[CapabilityEvidenceAssessment, ...]:
        if any(not isinstance(item, CapabilityEvidenceAssessment) for item in values):
            raise ValueError("evidence_assessments must contain CapabilityEvidenceAssessment values")
        key = lambda item: (item.capability_claim, item.model_dump_json())
        return tuple(sorted({key(item): item for item in values}.values(), key=key))

    @field_validator("issues", mode="after")
    @classmethod
    def issues_are_canonical(
        cls, values: tuple[InstantiationIssue, ...]
    ) -> tuple[InstantiationIssue, ...]:
        if any(not isinstance(item, InstantiationIssue) for item in values):
            raise ValueError("issues must contain InstantiationIssue values")
        key = lambda item: (
            item.issue_id,
            item.topology.value if item.topology else "",
            item.role.value if item.role else "",
            item.reason,
        )
        return tuple(sorted({key(item): item for item in values}.values(), key=key))


_MODALITY_MAP: Final[dict[WorkloadModality, ModelModality]] = {
    WorkloadModality.TEXT: ModelModality.TEXT,
    WorkloadModality.IMAGE: ModelModality.IMAGE,
    WorkloadModality.AUDIO: ModelModality.AUDIO,
    WorkloadModality.VIDEO: ModelModality.VIDEO,
    WorkloadModality.STRUCTURED_DATA: ModelModality.STRUCTURED_DATA,
}


def _record_order(record: ModelCapabilityRecord) -> tuple[str, str, str, str]:
    return record.provider, record.model_id, record.family, record.revision


def _phase4_modalities(
    request: CompositionInstantiationRequest,
) -> tuple[ModelModality, ...]:
    profile = request.intelligence_result.profile
    signals = request.intelligence_result.signals
    assert profile is not None and signals is not None
    values: set[ModelModality] = set()
    for modality in profile.modalities:
        if modality is WorkloadModality.MULTIMODAL:
            for explicit in signals.explicit_modalities:
                try:
                    values.add(ModelModality(explicit))
                except ValueError:
                    if explicit == WorkloadModality.CODE.value:
                        values.add(ModelModality.TEXT)
        elif modality is WorkloadModality.CODE:
            values.add(ModelModality.TEXT)
        elif modality in _MODALITY_MAP:
            values.add(_MODALITY_MAP[modality])
    if not values:
        raise ValueError("workload modalities cannot be mapped to Phase 4 contracts")
    return tuple(sorted(values, key=lambda item: item.value))


def _artifact_contracts(
    role: CompositionRole,
    modalities: tuple[ModelModality, ...],
    structured_output: bool,
) -> tuple[tuple[CompositionArtifactContract, ...], tuple[CompositionArtifactContract, ...]]:
    input_artifact = CompositionArtifactContract(
        artifact_id=f"{role.value}-input",
        modalities=modalities,
        requires_structured_output=False,
        evidence=("derived from certified Phase 2 modality and Phase 3 graph contracts",),
    )
    output_artifact = CompositionArtifactContract(
        artifact_id=f"{role.value}-output",
        modalities=(ModelModality.TEXT,),
        requires_structured_output=structured_output,
        evidence=("derived from certified Phase 2 output and Phase 3 graph contracts",),
    )
    return (input_artifact,), (output_artifact,)


def _derived_role_requirement(
    request: CompositionInstantiationRequest,
    pattern: CertifiedCompositionPattern,
    role: CompositionRole,
) -> CompositionRoleRequirement:
    profile = request.intelligence_result.profile
    assert profile is not None
    modalities = _phase4_modalities(request)
    capabilities = set(profile.required_capabilities)
    for graph_node in request.graph.nodes:
        capabilities.update(graph_node.required_capabilities)
    specialized = pattern.topology is not CertifiedTopology.SINGLE
    if specialized and role is CompositionRole.PRIMARY:
        capabilities.difference_update(
            {
                ComputationalCapability.RETRIEVAL,
                ComputationalCapability.TOOL_USE,
                ComputationalCapability.CODE_EXECUTION,
            }
        )

    if role is CompositionRole.RETRIEVAL_AUGMENTER:
        capabilities = {ComputationalCapability.RETRIEVAL}
    elif role is CompositionRole.TOOL_MODEL:
        capabilities = {
            capability
            for capability in capabilities
            if capability in (
                ComputationalCapability.TOOL_USE,
                ComputationalCapability.CODE_EXECUTION,
            )
        } or {ComputationalCapability.TOOL_USE}
    elif role in (CompositionRole.VERIFIER,):
        capabilities = {
            capability
            for capability in capabilities
            if capability
            not in (
                ComputationalCapability.RETRIEVAL,
                ComputationalCapability.TOOL_USE,
                ComputationalCapability.CODE_EXECUTION,
            )
        }
    elif role in (CompositionRole.SPECIALIST, CompositionRole.CRITIC):
        raise ValueError(f"{role.value} requires an explicit role requirement")

    reasoning: set[ReasoningCapability] = set()
    if ComputationalCapability.REASONING in capabilities:
        reasoning.add(ReasoningCapability.GENERAL)
        if profile.reasoning_complexity in (
            ReasoningComplexity.HIGH,
            ReasoningComplexity.DEEP,
        ):
            reasoning.add(ReasoningCapability.MULTI_STEP)

    structured = ComputationalCapability.STRUCTURED_OUTPUT in capabilities
    tool_use = ComputationalCapability.TOOL_USE in capabilities or role is CompositionRole.TOOL_MODEL
    code_tool = ComputationalCapability.CODE_EXECUTION in capabilities
    required_output = (
        (ModelModality.STRUCTURED_DATA,) if structured else (ModelModality.TEXT,)
    )
    requirement_ids = tuple(
        sorted(
            {
                *(f"capability:{item.value}" for item in capabilities),
                *(f"input:{item.value}" for item in modalities),
                *(f"output:{item.value}" for item in required_output),
            }
        )
    )
    requirements = ModelCapabilityRequirements(
        required_input_modalities=modalities,
        required_output_modalities=required_output,
        required_reasoning_capabilities=tuple(reasoning),
        requires_tool_use=tool_use,
        requires_retrieval=ComputationalCapability.RETRIEVAL in capabilities,
        requires_code_understanding=code_tool,
        requires_structured_tool_arguments=code_tool,
        requires_tool_result_consumption=code_tool,
        requires_json_output=structured,
        requires_schema_constrained_output=structured,
        evidence=(
            f"deterministic {role.value} requirements derived from certified Phase 2/3 contracts",
        ),
    )
    inputs, outputs = _artifact_contracts(role, modalities, structured)
    return CompositionRoleRequirement(
        role=role,
        requirement_ids=requirement_ids,
        requirements=requirements,
        input_artifacts=inputs,
        output_artifacts=outputs,
        provenance=(
            CompositionProvenanceReference(
                source_phase="phase2",
                artifact_id=request.intelligence_result.request_id,
                evidence="requirements derived from certified workload intelligence",
            ),
            CompositionProvenanceReference(
                source_phase="phase3",
                artifact_id=request.graph.graph_id,
                evidence="requirements derived from certified logical graph",
            ),
        ),
    )


def derive_role_requirements(
    request: CompositionInstantiationRequest,
    pattern: CertifiedCompositionPattern,
) -> tuple[CompositionRoleRequirement, ...]:
    """Return one explicit hard-requirement contract per role in a pattern."""

    if not isinstance(request, CompositionInstantiationRequest):
        raise ValueError("request must be a CompositionInstantiationRequest")
    if not isinstance(pattern, CertifiedCompositionPattern):
        raise ValueError("pattern must be a CertifiedCompositionPattern")
    explicit = {item.role: item for item in request.role_requirements}
    requirements: list[CompositionRoleRequirement] = []
    seen: set[CompositionRole] = set()
    for slot in pattern.slots:
        if slot.role in seen:
            continue
        seen.add(slot.role)
        requirements.append(
            explicit.get(slot.role)
            or _derived_role_requirement(request, pattern, slot.role)
        )
    return tuple(requirements)


def _applicable_patterns(
    request: CompositionInstantiationRequest,
) -> tuple[CertifiedCompositionPattern, ...]:
    node_types = {item.node_type for item in request.graph.nodes}
    explicit_roles = {item.role for item in request.role_requirements}
    applicable: list[CertifiedCompositionPattern] = []
    for pattern in get_certified_patterns():
        topology = pattern.topology
        applies = False
        if topology is CertifiedTopology.SINGLE:
            applies = not request.composition_required
        elif topology is CertifiedTopology.PRIMARY_VERIFIER:
            applies = GraphNodeType.VALIDATION in node_types
        elif topology is CertifiedTopology.PRIMARY_CRITIC:
            applies = CompositionRole.CRITIC in explicit_roles
        elif topology is CertifiedTopology.PRIMARY_SPECIALIST_PRIMARY:
            applies = CompositionRole.SPECIALIST in explicit_roles
        elif topology is CertifiedTopology.PRIMARY_RETRIEVAL_PRIMARY:
            applies = GraphNodeType.RETRIEVAL in node_types
        elif topology is CertifiedTopology.PRIMARY_TOOL_PRIMARY:
            applies = GraphNodeType.TOOL in node_types
        elif topology is CertifiedTopology.PRIMARY_SPECIALIST_VERIFIER:
            applies = (
                CompositionRole.SPECIALIST in explicit_roles
                and GraphNodeType.VALIDATION in node_types
            )
        if applies:
            applicable.append(pattern)
    return tuple(applicable)


def _assess_constraints(
    request: CompositionInstantiationRequest,
) -> tuple[CapabilityEvidenceAssessment, ...]:
    return tuple(
        assess_capability_evidence(item.evidence, item.assessment_requirements)
        for item in request.evidence_constraints
    )


def _blocked_roles(
    request: CompositionInstantiationRequest,
    assessments: tuple[CapabilityEvidenceAssessment, ...],
) -> frozenset[CompositionRole]:
    by_claim = {item.capability_claim: item for item in assessments}
    return frozenset(
        constraint.role
        for constraint in request.evidence_constraints
        if constraint.assessment_requirements.requires_evidence
        and by_claim[constraint.capability_claim].status
        is not EvidenceAssessmentStatus.ACCEPTABLE
    )


def _bindings(
    pattern: CertifiedCompositionPattern,
    candidates_by_role: dict[CompositionRole, tuple[ModelCapabilityRecord, ...]],
) -> Iterator[tuple[ModelCapabilityRecord, ...]]:
    choices = tuple(candidates_by_role[slot.role] for slot in pattern.slots)
    for combination in product(*choices):
        identity_groups: dict[str, tuple[str, str, str, str]] = {}
        valid = True
        for slot, record in zip(pattern.slots, combination, strict=True):
            if slot.identity_group is None:
                continue
            identity = _record_order(record)
            prior = identity_groups.setdefault(slot.identity_group, identity)
            if prior != identity:
                valid = False
                break
        if valid:
            yield combination


def _semantic_composition_id(
    request: CompositionInstantiationRequest,
    pattern: CertifiedCompositionPattern,
    requirements_by_role: dict[CompositionRole, CompositionRoleRequirement],
    binding: tuple[ModelCapabilityRecord, ...],
) -> str:
    payload = {
        "schema_version": COMPOSITION_SCHEMA_VERSION,
        "request_id": request.intelligence_result.request_id,
        "workload_id": request.intelligence_result.workload_id,
        "session_id": request.intelligence_result.session_id,
        "graph_id": request.graph.graph_id,
        "topology": pattern.topology.value,
        "stages": [
            {
                "stage_id": slot.stage_id,
                "role": slot.role.value,
                "model_identity": {
                    "provider": record.provider,
                    "model_id": record.model_id,
                    "family": record.family,
                    "revision": record.revision,
                },
                "requirement_ids": list(
                    requirements_by_role[slot.role].requirement_ids
                ),
                "requirements": requirements_by_role[
                    slot.role
                ].requirements.model_dump(mode="json"),
            }
            for slot, record in zip(pattern.slots, binding, strict=True)
        ],
        "edges": [
            {
                "source": item.source_stage_id,
                "target": item.target_stage_id,
                "dependency_type": item.dependency_type.value,
            }
            for item in pattern.edges
        ],
    }
    canonical = dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return f"sha256:{sha256(canonical.encode('utf-8')).hexdigest()}"


def _draft(
    request: CompositionInstantiationRequest,
    pattern: CertifiedCompositionPattern,
    role_requirements: tuple[CompositionRoleRequirement, ...],
    binding: tuple[ModelCapabilityRecord, ...],
    assessments: tuple[CapabilityEvidenceAssessment, ...],
) -> CompositionCandidateDraft:
    requirements_by_role = {item.role: item for item in role_requirements}
    relevant_roles = {slot.role for slot in pattern.slots}
    relevant_assessments = tuple(
        assessment
        for constraint, assessment in zip(
            request.evidence_constraints, assessments, strict=True
        )
        if constraint.role in relevant_roles
    )
    nodes = []
    for slot, record in zip(pattern.slots, binding, strict=True):
        role_requirement = requirements_by_role[slot.role]
        identity_text = "/".join(_record_order(record))
        node_provenance = tuple(
            sorted(
                {
                    _provenance_key(item): item
                    for item in (
                        *role_requirement.provenance,
                        CompositionProvenanceReference(
                            source_phase="phase4",
                            artifact_id=identity_text,
                            evidence="exact model capability record preserved from registry",
                        ),
                        CompositionProvenanceReference(
                            source_phase="phase4",
                            artifact_id=f"compatibility:{identity_text}",
                            evidence="Phase 4 discovery admitted the exact compatible record",
                        ),
                    )
                }.values(),
                key=_provenance_key,
            )
        )
        nodes.append(
            CompositionNode(
                stage_id=slot.stage_id,
                role=slot.role,
                model_record=record,
                requirements=role_requirement.requirements,
                input_artifacts=role_requirement.input_artifacts,
                output_artifacts=role_requirement.output_artifacts,
                justifications=tuple(
                    CapabilityJustification(
                        requirement_id=requirement_id,
                        capability_field="phase4_compatibility",
                        declared_value="compatible",
                        reason="Phase 4 discovery confirmed this exact record satisfies the hard requirement set",
                    )
                    for requirement_id in role_requirement.requirement_ids
                ),
                provenance=node_provenance,
            )
        )

    edges = tuple(
        CompositionEdge(
            source_stage_id=item.source_stage_id,
            target_stage_id=item.target_stage_id,
            dependency_type=item.dependency_type,
            artifact_id=requirements_by_role[
                next(
                    slot.role
                    for slot in pattern.slots
                    if slot.stage_id == item.source_stage_id
                )
            ].output_artifacts[0].artifact_id,
            evidence=(
                f"certified pattern {pattern.pattern_id} declares this logical handoff",
            ),
        )
        for item in pattern.edges
    )
    all_requirement_ids = tuple(
        sorted(
            {
                requirement_id
                for item in role_requirements
                for requirement_id in item.requirement_ids
            }
        )
    )
    draft_provenance = (
        CompositionProvenanceReference(
            source_phase="phase2",
            artifact_id=request.intelligence_result.request_id,
            evidence="certified workload identity and intelligence preserved",
        ),
        CompositionProvenanceReference(
            source_phase="phase3",
            artifact_id=request.graph.graph_id,
            evidence="certified logical graph and readiness preserved",
        ),
        CompositionProvenanceReference(
            source_phase="phase4",
            artifact_id=request.registry.fingerprint,
            evidence="exact immutable registry snapshot fingerprint preserved",
        ),
        CompositionProvenanceReference(
            source_phase="phase5",
            artifact_id=pattern.pattern_id,
            evidence="candidate instantiated from an exact certified pattern",
        ),
        CompositionProvenanceReference(
            source_phase="phase5",
            artifact_id=f"reason:{pattern.topology.value}",
            evidence="explicit certified graph and role requirements made this topology applicable",
        ),
    )
    return CompositionCandidateDraft(
        composition_id=_semantic_composition_id(
            request, pattern, requirements_by_role, binding
        ),
        request_id=request.intelligence_result.request_id,
        workload_id=request.intelligence_result.workload_id,
        session_id=request.intelligence_result.session_id,
        graph_id=request.graph.graph_id,
        pattern_id=pattern.pattern_id,
        topology=pattern.topology,
        nodes=tuple(nodes),
        edges=edges,
        satisfied_requirement_ids=all_requirement_ids,
        evidence_assessments=relevant_assessments,
        provenance=draft_provenance,
    )


def _instantiate(
    request: CompositionInstantiationRequest,
) -> tuple[
    tuple[CompositionCandidateDraft, ...],
    tuple[CertifiedTopology, ...],
    tuple[CapabilityEvidenceAssessment, ...],
    tuple[InstantiationIssue, ...],
]:
    patterns = _applicable_patterns(request)
    assessments = _assess_constraints(request)
    blocked_roles = _blocked_roles(request, assessments)
    drafts: list[CompositionCandidateDraft] = []
    issues: list[InstantiationIssue] = []

    for pattern in patterns:
        try:
            role_requirements = derive_role_requirements(request, pattern)
        except ValueError as error:
            issues.append(
                InstantiationIssue(
                    issue_id="unsupported_role_requirement",
                    topology=pattern.topology,
                    reason=str(error),
                )
            )
            continue
        candidates_by_role: dict[CompositionRole, tuple[ModelCapabilityRecord, ...]] = {}
        for role_requirement in role_requirements:
            if role_requirement.role in blocked_roles:
                candidates_by_role[role_requirement.role] = ()
                issues.append(
                    InstantiationIssue(
                        issue_id="required_evidence_unacceptable",
                        role=role_requirement.role,
                        topology=pattern.topology,
                        reason="explicit hard evidence requirement is not acceptable",
                    )
                )
                continue
            discovery = discover_capabilities(
                CapabilityDiscoveryQuery(
                    registry=request.registry,
                    requirements=role_requirement.requirements,
                )
            )
            candidates_by_role[role_requirement.role] = tuple(
                sorted(
                    (item.record for item in discovery.candidates),
                    key=_record_order,
                )
            )
            if not discovery.candidates:
                issues.append(
                    InstantiationIssue(
                        issue_id="no_compatible_record",
                        role=role_requirement.role,
                        topology=pattern.topology,
                        reason="Phase 4 discovery found no record satisfying the exact hard requirements",
                    )
                )
        if any(not candidates_by_role[item.role] for item in role_requirements):
            continue
        for binding in _bindings(pattern, candidates_by_role):
            drafts.append(
                _draft(request, pattern, role_requirements, binding, assessments)
            )
    return (
        tuple(drafts),
        tuple(item.topology for item in patterns),
        assessments,
        tuple(issues),
    )


def iter_composition_candidate_drafts(
    request: CompositionInstantiationRequest,
) -> Iterator[CompositionCandidateDraft]:
    """Yield candidate drafts in certified-pattern and exact-identity order."""

    if not isinstance(request, CompositionInstantiationRequest):
        raise ValueError("request must be a CompositionInstantiationRequest")
    drafts, _, _, _ = _instantiate(request)
    yield from drafts


def instantiate_composition_candidates(
    request: CompositionInstantiationRequest,
) -> CompositionInstantiationResult:
    """Instantiate zero, one, or many drafts without ranking or final validation."""

    if not isinstance(request, CompositionInstantiationRequest):
        raise ValueError("request must be a CompositionInstantiationRequest")
    drafts, topologies, assessments, issues = _instantiate(request)
    return CompositionInstantiationResult(
        drafts=drafts,
        applicable_topologies=topologies,
        evidence_assessments=assessments,
        issues=issues,
    )
