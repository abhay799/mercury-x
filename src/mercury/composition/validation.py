"""Independent fail-closed validation for model-composition drafts."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from enum import Enum
from hashlib import sha256
from json import dumps
from typing import Any, Final, Mapping

from pydantic import SkipValidation, field_validator, model_validator

from mercury.composition.contracts import (
    COMPOSITION_SCHEMA_VERSION,
    MAX_COMPOSITION_NODES,
    CertifiedTopology,
    CompositionCandidate,
    CompositionCandidateDraft,
    CompositionRejection,
    CompositionRole,
    CompositionValidity,
    canonical_model_identity,
)
from mercury.composition.patterns import CertifiedCompositionPattern, get_certified_pattern
from mercury.contracts.base import ContractModel
from mercury.graph.models import ExecutionGraph
from mercury.graph.readiness import GraphReadinessResult, GraphReadinessStatus
from mercury.intelligence.pipeline import PipelineStatus, WorkloadIntelligencePipelineResult
from mercury.models.capabilities import ModelCapabilityRecord, ModelModality
from mercury.models.compatibility import CompatibilityStatus, evaluate_compatibility
from mercury.models.evidence import CapabilityEvidenceAssessment, EvidenceAssessmentStatus
from mercury.models.registry import ModelCapabilityRegistry


class CompositionValidationStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"


def _nonblank(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be nonblank")
    return value


class CompositionValidationIssue(ContractModel):
    issue_id: str
    stage_id: str | None = None
    edge_reference: str | None = None
    violated_field: str
    reason: str

    @field_validator("issue_id", "violated_field", "reason")
    @classmethod
    def required_values_are_nonblank(cls, value: str) -> str:
        return _nonblank(value, "validation issue value")

    @field_validator("stage_id", "edge_reference")
    @classmethod
    def optional_values_are_nonblank(cls, value: str | None) -> str | None:
        return None if value is None else _nonblank(value, "validation issue reference")


class CompositionValidationContext(ContractModel):
    intelligence_result: WorkloadIntelligencePipelineResult
    graph: ExecutionGraph
    readiness_result: GraphReadinessResult
    registry: ModelCapabilityRegistry
    hard_requirement_ids: tuple[str, ...]

    @field_validator("hard_requirement_ids", mode="after")
    @classmethod
    def requirement_ids_are_canonical(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if any(not isinstance(item, str) or not item.strip() for item in values):
            raise ValueError("hard_requirement_ids must contain nonblank values")
        normalized = tuple(sorted(set(values)))
        if not normalized:
            raise ValueError("hard_requirement_ids must not be empty")
        return normalized

    @model_validator(mode="after")
    def upstream_state_is_consistent(self) -> CompositionValidationContext:
        if self.intelligence_result.status is PipelineStatus.FAIL:
            raise ValueError("failed workload intelligence cannot validate composition")
        if self.readiness_result.status is not GraphReadinessStatus.READY:
            raise ValueError("graph readiness must be READY")
        identity = (
            self.intelligence_result.request_id,
            self.intelligence_result.workload_id,
            self.intelligence_result.session_id,
        )
        if (self.graph.request_id, self.graph.workload_id, self.graph.session_id) != identity:
            raise ValueError("graph identity must match workload intelligence")
        if (
            self.readiness_result.request_id,
            self.readiness_result.workload_id,
            self.readiness_result.session_id,
        ) != identity:
            raise ValueError("readiness identity must match workload intelligence")
        if self.readiness_result.graph_id != self.graph.graph_id:
            raise ValueError("readiness graph_id must match graph")
        if not self.graph.provenance:
            raise ValueError("source graph provenance must not be empty")
        return self


class CompositionValidationResult(ContractModel):
    status: CompositionValidationStatus
    candidate: SkipValidation[CompositionCandidate]
    issues: tuple[CompositionValidationIssue, ...]
    checked_invariant_ids: tuple[str, ...]

    @field_validator("issues", mode="after")
    @classmethod
    def issues_are_canonical(
        cls, values: tuple[CompositionValidationIssue, ...]
    ) -> tuple[CompositionValidationIssue, ...]:
        if any(not isinstance(item, CompositionValidationIssue) for item in values):
            raise ValueError("issues must contain CompositionValidationIssue values")
        key = lambda item: (
            item.issue_id,
            item.stage_id or "",
            item.edge_reference or "",
            item.violated_field,
            item.reason,
        )
        return tuple(sorted({key(item): item for item in values}.values(), key=key))

    @field_validator("checked_invariant_ids", mode="after")
    @classmethod
    def invariant_ids_are_canonical(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if any(not isinstance(item, str) or not item.strip() for item in values):
            raise ValueError("checked_invariant_ids must contain nonblank values")
        normalized = tuple(sorted(set(values)))
        if not normalized:
            raise ValueError("checked_invariant_ids must not be empty")
        return normalized

    @model_validator(mode="after")
    def status_matches_candidate(self) -> CompositionValidationResult:
        if not isinstance(self.candidate, CompositionCandidate):
            raise ValueError("candidate must be a CompositionCandidate")
        if self.status is CompositionValidationStatus.PASS:
            if self.issues or self.candidate.validity is not CompositionValidity.VALID:
                raise ValueError("PASS requires a VALID candidate and no issues")
        elif not self.issues or self.candidate.validity is not CompositionValidity.REJECTED:
            raise ValueError("FAIL requires a REJECTED candidate and issues")
        return self


_CHECKED_INVARIANTS: Final[tuple[str, ...]] = tuple(
    sorted(
        {
            "schema_version",
            "identity_consistency",
            "composition_id",
            "pattern_conformance",
            "certified_role",
            "dag_structure",
            "entry_exit_reachability",
            "repeated_primary_identity",
            "registry_identity",
            "capability_compatibility",
            "requirement_coverage",
            "handoff_compatibility",
            "required_evidence",
            "provenance",
            "capability_justification",
            "boundary_compliance",
        }
    )
)

_FORBIDDEN_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "rank",
        "score",
        "winner",
        "preferred_candidate",
        "selected_model",
        "fallback_ordering",
        "graph_node_assignment",
        "cost_optimization",
        "latency_optimization",
        "quality_optimization",
        "hardware",
        "device",
        "placement",
        "scheduler_assignment",
        "runtime_invocation",
    }
)


def _issue(
    issue_id: str,
    violated_field: str,
    reason: str,
    *,
    stage_id: str | None = None,
    edge_reference: str | None = None,
) -> CompositionValidationIssue:
    return CompositionValidationIssue(
        issue_id=issue_id,
        stage_id=stage_id,
        edge_reference=edge_reference,
        violated_field=violated_field,
        reason=reason,
    )


def _safe_stage_id(node: object) -> str | None:
    value = getattr(node, "stage_id", None)
    return value if isinstance(value, str) and value.strip() else None


def _safe_edge_reference(edge: object) -> str | None:
    source = getattr(edge, "source_stage_id", None)
    target = getattr(edge, "target_stage_id", None)
    if isinstance(source, str) and source.strip() and isinstance(target, str) and target.strip():
        return f"{source}->{target}"
    return None


def _pattern_for(draft: CompositionCandidateDraft) -> CertifiedCompositionPattern | None:
    topology = getattr(draft, "topology", None)
    if not isinstance(topology, CertifiedTopology):
        return None
    try:
        return get_certified_pattern(topology)
    except ValueError:
        return None


def _semantic_composition_id(
    draft: CompositionCandidateDraft,
    pattern: CertifiedCompositionPattern,
) -> str | None:
    nodes = getattr(draft, "nodes", ())
    if not isinstance(nodes, tuple):
        return None
    nodes_by_id = {
        stage_id: item
        for item in nodes
        if (stage_id := _safe_stage_id(item)) is not None
    }
    if any(slot.stage_id not in nodes_by_id for slot in pattern.slots):
        return None
    try:
        payload = {
            "schema_version": COMPOSITION_SCHEMA_VERSION,
            "request_id": draft.request_id,
            "workload_id": draft.workload_id,
            "session_id": draft.session_id,
            "graph_id": draft.graph_id,
            "topology": pattern.topology.value,
            "stages": [
                {
                    "stage_id": slot.stage_id,
                    "role": slot.role.value,
                    "model_identity": {
                        "provider": nodes_by_id[slot.stage_id].model_record.provider,
                        "model_id": nodes_by_id[slot.stage_id].model_record.model_id,
                        "family": nodes_by_id[slot.stage_id].model_record.family,
                        "revision": nodes_by_id[slot.stage_id].model_record.revision,
                    },
                    "requirement_ids": sorted(
                        item.requirement_id
                        for item in nodes_by_id[slot.stage_id].justifications
                    ),
                    "requirements": nodes_by_id[
                        slot.stage_id
                    ].requirements.model_dump(mode="json"),
                }
                for slot in pattern.slots
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
    except (AttributeError, TypeError, ValueError):
        return None
    return f"sha256:{sha256(canonical.encode('utf-8')).hexdigest()}"


def _topology_issues(
    draft: CompositionCandidateDraft,
    pattern: CertifiedCompositionPattern | None,
) -> list[CompositionValidationIssue]:
    issues: list[CompositionValidationIssue] = []
    nodes = getattr(draft, "nodes", ())
    edges = getattr(draft, "edges", ())
    if not isinstance(nodes, tuple) or not nodes or len(nodes) > MAX_COMPOSITION_NODES:
        issues.append(_issue("dag_structure", "nodes", "candidate must contain one to three stages"))
        return issues

    stage_ids = tuple(_safe_stage_id(item) for item in nodes)
    valid_ids = {item for item in stage_ids if item is not None}
    if None in stage_ids or len(valid_ids) != len(stage_ids):
        issues.append(_issue("dag_structure", "stage_id", "stage identifiers must be nonblank and unique"))
    for node in nodes:
        if not isinstance(getattr(node, "role", None), CompositionRole):
            issues.append(
                _issue(
                    "certified_role",
                    "role",
                    "every stage must use a certified composition role",
                    stage_id=_safe_stage_id(node),
                )
            )

    if not isinstance(edges, tuple):
        issues.append(_issue("dag_structure", "edges", "candidate edges must be an immutable tuple"))
        return issues
    incoming = {stage_id: 0 for stage_id in valid_ids}
    outgoing = {stage_id: [] for stage_id in valid_ids}
    undirected = {stage_id: set() for stage_id in valid_ids}
    valid_edges = []
    for edge in edges:
        source = getattr(edge, "source_stage_id", None)
        target = getattr(edge, "target_stage_id", None)
        reference = _safe_edge_reference(edge)
        if source not in valid_ids or target not in valid_ids:
            issues.append(
                _issue("dag_structure", "edge_reference", "edge references an undeclared stage", edge_reference=reference)
            )
            continue
        if source == target:
            issues.append(
                _issue("dag_structure", "self_edge", "self-edges are forbidden", stage_id=source, edge_reference=reference)
            )
            continue
        valid_edges.append(edge)
        incoming[target] += 1
        outgoing[source].append(target)
        undirected[source].add(target)
        undirected[target].add(source)

    if len(valid_ids) > 1 and any(not item for item in undirected.values()):
        issues.append(_issue("dag_structure", "orphan_stage", "every stage must participate in the connected flow"))
    if valid_ids:
        seen: set[str] = set()
        pending = [min(valid_ids)]
        while pending:
            current = pending.pop()
            if current in seen:
                continue
            seen.add(current)
            pending.extend(sorted(undirected[current] - seen, reverse=True))
        if seen != valid_ids:
            issues.append(_issue("dag_structure", "connectedness", "candidate stages must form one connected graph"))

        counts = dict(incoming)
        ready = sorted(item for item, count in counts.items() if count == 0)
        visited = []
        while ready:
            current = ready.pop(0)
            visited.append(current)
            for target in sorted(outgoing[current]):
                counts[target] -= 1
                if counts[target] == 0:
                    ready.append(target)
                    ready.sort()
        if len(visited) != len(valid_ids):
            issues.append(_issue("dag_structure", "cycle", "candidate graph must be acyclic"))
        elif len(valid_ids) > 1:
            entries = tuple(item for item in valid_ids if incoming[item] == 0)
            exits = tuple(item for item in valid_ids if not outgoing[item])
            if len(entries) != 1 or len(exits) != 1:
                issues.append(
                    _issue("entry_exit_reachability", "entry_exit", "candidate requires one complete entry-to-exit path")
                )

    if pattern is None:
        issues.append(_issue("pattern_conformance", "topology", "topology is not certified"))
        return issues
    if getattr(draft, "pattern_id", None) != pattern.pattern_id:
        issues.append(_issue("pattern_conformance", "pattern_id", "pattern identity does not match certified topology"))
    expected_slots = tuple((item.stage_id, item.role) for item in pattern.slots)
    actual_by_id = {
        stage_id: getattr(item, "role", None)
        for item in nodes
        if (stage_id := _safe_stage_id(item)) is not None
    }
    actual_slots = tuple((item.stage_id, actual_by_id.get(item.stage_id)) for item in pattern.slots)
    if set(actual_by_id) != {item.stage_id for item in pattern.slots} or actual_slots != expected_slots:
        issues.append(_issue("pattern_conformance", "slots", "stage identities and roles must exactly match the certified pattern"))
    expected_edges = {
        (item.source_stage_id, item.target_stage_id, item.dependency_type)
        for item in pattern.edges
    }
    actual_edges = {
        (
            getattr(item, "source_stage_id", None),
            getattr(item, "target_stage_id", None),
            getattr(item, "dependency_type", None),
        )
        for item in valid_edges
    }
    if actual_edges != expected_edges or len(valid_edges) != len(pattern.edges):
        issues.append(_issue("pattern_conformance", "edges", "logical edges must exactly match the certified pattern"))
    return issues


def _identity_and_capability_issues(
    draft: CompositionCandidateDraft,
    context: CompositionValidationContext,
    pattern: CertifiedCompositionPattern | None,
) -> list[CompositionValidationIssue]:
    issues: list[CompositionValidationIssue] = []
    identity = (
        context.intelligence_result.request_id,
        context.intelligence_result.workload_id,
        context.intelligence_result.session_id,
        context.graph.graph_id,
    )
    draft_identity = tuple(
        getattr(draft, field_name, None)
        for field_name in ("request_id", "workload_id", "session_id", "graph_id")
    )
    if any(not isinstance(item, str) or not item.strip() for item in draft_identity) or draft_identity != identity:
        issues.append(_issue("identity_consistency", "identity", "candidate and certified upstream identities must match exactly"))

    nodes = getattr(draft, "nodes", ())
    if not isinstance(nodes, tuple):
        return issues
    for node in nodes:
        stage_id = _safe_stage_id(node)
        record = getattr(node, "model_record", None)
        requirements = getattr(node, "requirements", None)
        if not isinstance(record, ModelCapabilityRecord):
            issues.append(_issue("registry_identity", "model_record", "stage must preserve an exact Phase 4 record", stage_id=stage_id))
            continue
        try:
            registered = context.registry.lookup(
                record.provider, record.model_id, record.family, record.revision
            )
        except Exception:
            registered = None
        if registered is None or registered != record:
            issues.append(_issue("registry_identity", "model_record", "exact provider/model/family/revision record is absent or changed", stage_id=stage_id))
        try:
            compatibility = evaluate_compatibility(record, requirements)
        except (TypeError, ValueError, AttributeError):
            compatibility = None
        if compatibility is None or compatibility.status is not CompatibilityStatus.COMPATIBLE:
            issues.append(_issue("capability_compatibility", "requirements", "exact Phase 4 record does not cover the stage hard requirements", stage_id=stage_id))

    if pattern is not None and pattern.topology in {
        CertifiedTopology.PRIMARY_SPECIALIST_PRIMARY,
        CertifiedTopology.PRIMARY_RETRIEVAL_PRIMARY,
        CertifiedTopology.PRIMARY_TOOL_PRIMARY,
    }:
        primary_records = [
            getattr(item, "model_record", None)
            for item in nodes
            if getattr(item, "role", None) is CompositionRole.PRIMARY
        ]
        identities = []
        for record in primary_records:
            try:
                identities.append(canonical_model_identity(record))
            except ValueError:
                pass
        if len(identities) != 2 or identities[0] != identities[1]:
            issues.append(_issue("repeated_primary_identity", "model_record", "return topology PRIMARY stages must preserve one exact identity and revision"))
    return issues


def _coverage_and_evidence_issues(
    draft: CompositionCandidateDraft,
    context: CompositionValidationContext,
) -> list[CompositionValidationIssue]:
    issues: list[CompositionValidationIssue] = []
    satisfied = getattr(draft, "satisfied_requirement_ids", ())
    if not isinstance(satisfied, tuple) or not set(context.hard_requirement_ids).issubset(set(satisfied)):
        issues.append(_issue("requirement_coverage", "satisfied_requirement_ids", "candidate does not cover every complete hard requirement id"))
    justified: set[str] = set()
    nodes = getattr(draft, "nodes", ())
    if isinstance(nodes, tuple):
        for node in nodes:
            justifications = getattr(node, "justifications", ())
            stage_id = _safe_stage_id(node)
            if not isinstance(justifications, tuple) or not justifications:
                issues.append(_issue("capability_justification", "justifications", "each stage requires nonblank capability justification", stage_id=stage_id))
                continue
            for item in justifications:
                values = (
                    getattr(item, "requirement_id", None),
                    getattr(item, "capability_field", None),
                    getattr(item, "declared_value", None),
                    getattr(item, "reason", None),
                )
                if any(not isinstance(value, str) or not value.strip() for value in values):
                    issues.append(_issue("capability_justification", "justifications", "capability justification fields must be nonblank", stage_id=stage_id))
                elif isinstance(values[0], str):
                    justified.add(values[0])
    if isinstance(satisfied, tuple) and not set(satisfied).issubset(justified):
        issues.append(_issue("requirement_coverage", "justifications", "every satisfied hard requirement requires a stage justification"))

    assessments = getattr(draft, "evidence_assessments", ())
    if not isinstance(assessments, tuple):
        issues.append(_issue("required_evidence", "evidence_assessments", "evidence assessments must be immutable contracts"))
    else:
        for assessment in assessments:
            if not isinstance(assessment, CapabilityEvidenceAssessment):
                issues.append(_issue("required_evidence", "evidence_assessments", "unsupported evidence assessment fails closed"))
                continue
            requirements = assessment.requirements
            explicitly_required = any(
                (
                    requirements.requires_evidence,
                    requirements.requires_current_valid,
                    requirements.requires_measured_or_observed,
                    requirements.requires_production_evidence,
                    requirements.reject_conflicts,
                )
            )
            if explicitly_required and assessment.status is not EvidenceAssessmentStatus.ACCEPTABLE:
                issues.append(_issue("required_evidence", "evidence_assessments", f"required evidence for {assessment.capability_claim} is {assessment.status.value}"))
    return issues


def _handoff_issues(draft: CompositionCandidateDraft) -> list[CompositionValidationIssue]:
    issues: list[CompositionValidationIssue] = []
    nodes = getattr(draft, "nodes", ())
    edges = getattr(draft, "edges", ())
    if not isinstance(nodes, tuple) or not isinstance(edges, tuple):
        return issues
    nodes_by_id = {
        stage_id: item
        for item in nodes
        if (stage_id := _safe_stage_id(item)) is not None
    }
    semantic_roles = {
        CompositionRole.RETRIEVAL_AUGMENTER: ("retrieval", "retrieval_handoff"),
        CompositionRole.TOOL_MODEL: ("tool", "tool_handoff"),
        CompositionRole.SPECIALIST: ("specialist", "specialist_handoff"),
    }
    for edge in edges:
        source_id = getattr(edge, "source_stage_id", None)
        target_id = getattr(edge, "target_stage_id", None)
        source = nodes_by_id.get(source_id)
        target = nodes_by_id.get(target_id)
        if source is None or target is None:
            continue
        reference = _safe_edge_reference(edge)
        outputs = getattr(source, "output_artifacts", ())
        inputs = getattr(target, "input_artifacts", ())
        artifact_id = getattr(edge, "artifact_id", None)
        carried = next(
            (item for item in outputs if getattr(item, "artifact_id", None) == artifact_id),
            None,
        )
        if carried is None:
            issues.append(_issue("handoff_compatibility", "artifact_id", "edge must carry an explicitly declared source output artifact", edge_reference=reference))
            if any(
                getattr(item, "requires_structured_output", False)
                or ModelModality.STRUCTURED_DATA in getattr(item, "modalities", ())
                for item in outputs
            ):
                issues.append(_issue("structured_handoff", "artifact_semantics", "structured artifact cannot be replaced by an undeclared generic artifact", edge_reference=reference))
        else:
            source_modalities = set(getattr(carried, "modalities", ()))
            target_modalities = {
                modality for item in inputs for modality in getattr(item, "modalities", ())
            }
            if not source_modalities or not source_modalities.intersection(target_modalities):
                issues.append(_issue("handoff_compatibility", "modalities", "source output and target input modalities are incompatible", edge_reference=reference))
            if getattr(carried, "requires_structured_output", False):
                target_structured = any(
                    getattr(item, "requires_structured_output", False)
                    or ModelModality.STRUCTURED_DATA in getattr(item, "modalities", ())
                    for item in inputs
                )
                if not target_structured:
                    issues.append(_issue("structured_handoff", "artifact_semantics", "structured artifact semantics must remain explicit at the target", edge_reference=reference))
        role = getattr(source, "role", None)
        if role in semantic_roles:
            marker, issue_id = semantic_roles[role]
            if not isinstance(artifact_id, str) or marker not in artifact_id:
                issues.append(_issue(issue_id, "artifact_semantics", f"{marker} artifact cannot be replaced by generic text", stage_id=source_id, edge_reference=reference))
    return issues


def _provenance_issues(draft: CompositionCandidateDraft) -> list[CompositionValidationIssue]:
    issues: list[CompositionValidationIssue] = []
    provenance = getattr(draft, "provenance", ())
    if not isinstance(provenance, tuple) or not provenance:
        issues.append(_issue("provenance", "provenance", "candidate provenance must be complete and nonempty"))
    else:
        for item in provenance:
            values = (
                getattr(item, "source_phase", None),
                getattr(item, "artifact_id", None),
                getattr(item, "evidence", None),
            )
            if any(not isinstance(value, str) or not value.strip() for value in values):
                issues.append(_issue("provenance", "provenance", "candidate provenance references must be nonblank"))
                break
    nodes = getattr(draft, "nodes", ())
    if isinstance(nodes, tuple):
        for node in nodes:
            node_provenance = getattr(node, "provenance", ())
            if not isinstance(node_provenance, tuple) or not node_provenance:
                issues.append(_issue("provenance", "node.provenance", "each stage requires complete provenance", stage_id=_safe_stage_id(node)))
    return issues


def _leaked_fields(value: object) -> tuple[str, ...]:
    leaked: set[str] = set()
    seen: set[int] = set()

    def visit(item: object) -> None:
        if item is None or isinstance(item, (str, bytes, int, float, bool, Enum)):
            return
        marker = id(item)
        if marker in seen:
            return
        seen.add(marker)
        if isinstance(item, Mapping):
            for key, nested in item.items():
                if isinstance(key, str) and key.lower() in _FORBIDDEN_FIELDS:
                    leaked.add(key.lower())
                visit(nested)
            return
        if isinstance(item, (tuple, list, set, frozenset)):
            for nested in item:
                visit(nested)
            return
        names: tuple[str, ...]
        if isinstance(item, ContractModel):
            names = tuple(item.__dict__)
        elif is_dataclass(item):
            names = tuple(field.name for field in fields(item))
        elif hasattr(item, "__dict__"):
            names = tuple(vars(item))
        else:
            return
        for name in names:
            if name.lower() in _FORBIDDEN_FIELDS:
                leaked.add(name.lower())
            try:
                visit(getattr(item, name))
            except AttributeError:
                continue

    visit(value)
    return tuple(sorted(leaked))


def _final_candidate(
    draft: CompositionCandidateDraft,
    issues: tuple[CompositionValidationIssue, ...],
) -> CompositionCandidate:
    validity = CompositionValidity.REJECTED if issues else CompositionValidity.VALID
    rejections = tuple(
        CompositionRejection(
            issue_id=item.issue_id,
            stage_id=item.stage_id,
            edge_reference=item.edge_reference,
            violated_invariant=item.violated_field,
            reason=item.reason,
        )
        for item in issues
    )
    values = dict(vars(draft))
    try:
        return CompositionCandidate(
            **values, validity=validity, rejection_reasons=rejections
        )
    except Exception:
        return CompositionCandidate.model_construct(
            **values, validity=validity, rejection_reasons=rejections
        )


def validate_composition_candidate(
    draft: CompositionCandidateDraft,
    context: CompositionValidationContext,
) -> CompositionValidationResult:
    """Validate one draft independently without mutation, repair, or preference."""

    if not isinstance(draft, CompositionCandidateDraft):
        raise ValueError("draft must be a CompositionCandidateDraft")
    if not isinstance(context, CompositionValidationContext):
        raise ValueError("context must be a CompositionValidationContext")

    issues: list[CompositionValidationIssue] = []
    if getattr(draft, "schema_version", None) != COMPOSITION_SCHEMA_VERSION:
        issues.append(_issue("schema_version", "schema_version", "composition schema version is unsupported"))

    pattern = _pattern_for(draft)
    issues.extend(_topology_issues(draft, pattern))
    issues.extend(_identity_and_capability_issues(draft, context, pattern))
    issues.extend(_coverage_and_evidence_issues(draft, context))
    issues.extend(_handoff_issues(draft))
    issues.extend(_provenance_issues(draft))

    expected_id = _semantic_composition_id(draft, pattern) if pattern is not None else None
    if expected_id is None or getattr(draft, "composition_id", None) != expected_id:
        issues.append(_issue("composition_id", "composition_id", "composition_id does not match canonical semantic content"))

    leaked = _leaked_fields(draft)
    if leaked:
        issues.append(_issue("boundary_compliance", "boundary", f"forbidden decision fields detected: {', '.join(leaked)}"))

    canonical_issues = CompositionValidationResult.issues_are_canonical(tuple(issues))
    candidate = _final_candidate(draft, canonical_issues)
    status = (
        CompositionValidationStatus.FAIL
        if canonical_issues
        else CompositionValidationStatus.PASS
    )
    return CompositionValidationResult(
        status=status,
        candidate=candidate,
        issues=canonical_issues,
        checked_invariant_ids=_CHECKED_INVARIANTS,
    )
