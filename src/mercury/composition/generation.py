"""Semantic deduplication and bounded generation for composition candidates."""

from __future__ import annotations

from hashlib import sha256
from json import dumps
from typing import Any

from pydantic import model_validator

from mercury.composition.contracts import (
    MAX_COMPOSITION_NODES,
    CompositionArtifactContract,
    CompositionCandidate,
    CompositionCandidateDraft,
    CompositionGenerationMetadata,
    CompositionGenerationPolicy,
    CompositionProvenanceReference,
    CompositionRejection,
    CompositionResult,
    CompositionResultStatus,
    CompositionValidity,
)
from mercury.composition.instantiation import (
    CompositionInstantiationRequest,
    iter_composition_candidate_drafts,
)
from mercury.composition.patterns import get_certified_pattern
from mercury.composition.validation import (
    CompositionValidationContext,
    CompositionValidationStatus,
    validate_composition_candidate,
)
from mercury.contracts.base import ContractModel
from mercury.models.compatibility import ModelCapabilityRequirements
from mercury.models.evidence import CapabilityEvidenceAssessment


class CompositionGenerationRequest(ContractModel):
    instantiation_request: CompositionInstantiationRequest
    policy: CompositionGenerationPolicy = CompositionGenerationPolicy()

    @model_validator(mode="after")
    def request_uses_certified_contracts(self) -> CompositionGenerationRequest:
        if not isinstance(self.instantiation_request, CompositionInstantiationRequest):
            raise ValueError("instantiation_request must use the Task 3 contract")
        if not isinstance(self.policy, CompositionGenerationPolicy):
            raise ValueError("policy must use the bounded generation contract")
        return self


def _enum_value(value: object) -> object:
    return getattr(value, "value", value)


def _artifact_semantics(item: object) -> dict[str, object]:
    if isinstance(item, dict):
        artifact_id = item.get("artifact_id")
        modalities = item.get("modalities", ())
        structured = item.get("requires_structured_output", False)
    else:
        artifact_id = getattr(item, "artifact_id", None)
        modalities = getattr(item, "modalities", ())
        structured = getattr(item, "requires_structured_output", False)
    return {
        "artifact_id": artifact_id,
        "modalities": sorted(str(_enum_value(value)) for value in modalities),
        "requires_structured_output": structured,
    }


def _requirement_semantics(requirements: object) -> dict[str, object]:
    if not isinstance(requirements, ModelCapabilityRequirements):
        raise ValueError("candidate stage requirements are malformed")
    values = requirements.model_dump(mode="json")
    values.pop("evidence", None)
    return values


def _node_semantics(node: object) -> dict[str, object]:
    role = getattr(node, "role", None)
    record = getattr(node, "model_record", None)
    if record is None:
        raise ValueError("candidate stage model record is malformed")
    return {
        "stage_id": getattr(node, "stage_id", None),
        "role": _enum_value(role),
        "model_identity": {
            "provider": getattr(record, "provider", None),
            "model_id": getattr(record, "model_id", None),
            "family": getattr(record, "family", None),
            "revision": getattr(record, "revision", None),
        },
        "requirements": _requirement_semantics(getattr(node, "requirements", None)),
        "input_artifacts": sorted(
            (_artifact_semantics(item) for item in getattr(node, "input_artifacts", ())),
            key=lambda item: str(item["artifact_id"]),
        ),
        "output_artifacts": sorted(
            (_artifact_semantics(item) for item in getattr(node, "output_artifacts", ())),
            key=lambda item: str(item["artifact_id"]),
        ),
    }


def _edge_semantics(edge: object) -> dict[str, object]:
    if isinstance(edge, dict):
        source = edge.get("source_stage_id")
        target = edge.get("target_stage_id")
        dependency_type = edge.get("dependency_type")
        artifact_id = edge.get("artifact_id")
    else:
        source = getattr(edge, "source_stage_id", None)
        target = getattr(edge, "target_stage_id", None)
        dependency_type = getattr(edge, "dependency_type", None)
        artifact_id = getattr(edge, "artifact_id", None)
    return {
        "source_stage_id": source,
        "target_stage_id": target,
        "dependency_type": _enum_value(dependency_type),
        "artifact_id": artifact_id,
    }


def semantic_candidate_signature(draft: CompositionCandidateDraft) -> str:
    """Hash candidate semantics while excluding provenance and evidence ordering."""

    if not isinstance(draft, CompositionCandidateDraft):
        raise ValueError("draft must be a CompositionCandidateDraft")
    nodes = getattr(draft, "nodes", ())
    if not isinstance(nodes, tuple) or not nodes or len(nodes) > MAX_COMPOSITION_NODES:
        raise ValueError("candidate node count exceeds the certified baseline")
    nodes_by_id = {getattr(item, "stage_id", None): item for item in nodes}
    topology = getattr(draft, "topology", None)
    try:
        pattern = get_certified_pattern(topology)
        ordered_nodes = tuple(
            nodes_by_id[item.stage_id]
            for item in pattern.slots
            if item.stage_id in nodes_by_id
        )
        if len(ordered_nodes) != len(nodes):
            ordered_nodes = tuple(sorted(nodes, key=lambda item: str(getattr(item, "stage_id", ""))))
    except (ValueError, KeyError, TypeError):
        ordered_nodes = tuple(sorted(nodes, key=lambda item: str(getattr(item, "stage_id", ""))))
    edges = getattr(draft, "edges", ())
    if not isinstance(edges, tuple):
        raise ValueError("candidate edges must be immutable")
    edge_values = sorted(
        (_edge_semantics(item) for item in edges),
        key=lambda item: (
            str(item["source_stage_id"]),
            str(item["target_stage_id"]),
            str(item["dependency_type"]),
            str(item["artifact_id"]),
        ),
    )
    payload = {
        "schema_version": getattr(draft, "schema_version", None),
        "topology": _enum_value(topology),
        "pattern_id": getattr(draft, "pattern_id", None),
        "nodes": [_node_semantics(item) for item in ordered_nodes],
        "edges": edge_values,
        "assigned_hard_requirements": sorted(
            getattr(draft, "satisfied_requirement_ids", ())
        ),
    }
    canonical = dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return f"sha256:{sha256(canonical.encode('utf-8')).hexdigest()}"


def _sorted_union(left: tuple[Any, ...], right: tuple[Any, ...], key: Any) -> tuple[Any, ...]:
    values = {key(item): item for item in (*left, *right)}
    return tuple(values[item_key] for item_key in sorted(values))


def _provenance_key(item: CompositionProvenanceReference) -> tuple[str, str, str]:
    return item.source_phase, item.artifact_id, item.evidence


def _assessment_key(item: CapabilityEvidenceAssessment) -> str:
    return item.model_dump_json()


def _merge_artifact(
    left: CompositionArtifactContract,
    right: CompositionArtifactContract,
) -> CompositionArtifactContract:
    if _artifact_semantics(left) != _artifact_semantics(right):
        raise ValueError("duplicate artifact semantics differ")
    evidence = tuple(sorted(set((*left.evidence, *right.evidence))))
    return left.model_copy(update={"evidence": evidence})


def _merge_artifact_tuple(
    left: tuple[CompositionArtifactContract, ...],
    right: tuple[CompositionArtifactContract, ...],
) -> tuple[CompositionArtifactContract, ...]:
    left_by_id = {item.artifact_id: item for item in left}
    right_by_id = {item.artifact_id: item for item in right}
    if set(left_by_id) != set(right_by_id):
        raise ValueError("duplicate artifact contracts differ")
    return tuple(
        _merge_artifact(left_by_id[artifact_id], right_by_id[artifact_id])
        for artifact_id in sorted(left_by_id)
    )


def _merge_requirements(
    left: ModelCapabilityRequirements,
    right: ModelCapabilityRequirements,
) -> ModelCapabilityRequirements:
    if _requirement_semantics(left) != _requirement_semantics(right):
        raise ValueError("duplicate hard requirements differ")
    evidence = tuple(sorted(set((*left.evidence, *right.evidence))))
    return left.model_copy(update={"evidence": evidence})


def _merge_nodes(left: tuple[Any, ...], right: tuple[Any, ...]) -> tuple[Any, ...]:
    left_by_id = {item.stage_id: item for item in left}
    right_by_id = {item.stage_id: item for item in right}
    if set(left_by_id) != set(right_by_id):
        raise ValueError("duplicate stage identities differ")
    merged = []
    for stage_id in sorted(left_by_id):
        left_node = left_by_id[stage_id]
        right_node = right_by_id[stage_id]
        if _node_semantics(left_node) != _node_semantics(right_node):
            raise ValueError("duplicate stage semantics differ")
        justifications = _sorted_union(
            left_node.justifications,
            right_node.justifications,
            lambda item: (
                item.requirement_id,
                item.capability_field,
                item.declared_value,
                item.reason,
            ),
        )
        provenance = _sorted_union(
            left_node.provenance, right_node.provenance, _provenance_key
        )
        merged.append(
            left_node.model_copy(
                update={
                    "requirements": _merge_requirements(
                        left_node.requirements, right_node.requirements
                    ),
                    "input_artifacts": _merge_artifact_tuple(
                        left_node.input_artifacts, right_node.input_artifacts
                    ),
                    "output_artifacts": _merge_artifact_tuple(
                        left_node.output_artifacts, right_node.output_artifacts
                    ),
                    "justifications": justifications,
                    "provenance": provenance,
                }
            )
        )
    return tuple(merged)


def _merge_edges(left: tuple[Any, ...], right: tuple[Any, ...]) -> tuple[Any, ...]:
    key = lambda item: (
        item.source_stage_id,
        item.target_stage_id,
        item.dependency_type.value,
        item.artifact_id,
    )
    left_by_key = {key(item): item for item in left}
    right_by_key = {key(item): item for item in right}
    if set(left_by_key) != set(right_by_key):
        raise ValueError("duplicate edge semantics differ")
    return tuple(
        left_by_key[item_key].model_copy(
            update={
                "evidence": tuple(
                    sorted(
                        set(
                            (*left_by_key[item_key].evidence, *right_by_key[item_key].evidence)
                        )
                    )
                )
            }
        )
        for item_key in sorted(left_by_key)
    )


def merge_duplicate_drafts(
    left: CompositionCandidateDraft,
    right: CompositionCandidateDraft,
) -> CompositionCandidateDraft:
    """Merge only evidence and provenance for semantically equal drafts."""

    if not isinstance(left, CompositionCandidateDraft) or not isinstance(
        right, CompositionCandidateDraft
    ):
        raise ValueError("duplicates must use CompositionCandidateDraft contracts")
    if semantic_candidate_signature(left) != semantic_candidate_signature(right):
        raise ValueError("candidate drafts are not semantic duplicates")
    if left.composition_id != right.composition_id:
        raise ValueError("semantic duplicates must preserve one composition_id")
    values = left.model_dump(mode="python")
    values.update(
        {
            "nodes": _merge_nodes(left.nodes, right.nodes),
            "edges": _merge_edges(left.edges, right.edges),
            "evidence_assessments": _sorted_union(
                left.evidence_assessments,
                right.evidence_assessments,
                _assessment_key,
            ),
            "provenance": _sorted_union(
                left.provenance, right.provenance, _provenance_key
            ),
        }
    )
    return CompositionCandidateDraft(**values)


def _node_limit_candidate(
    draft: CompositionCandidateDraft,
    max_nodes: int,
) -> CompositionCandidate:
    reason = CompositionRejection(
        issue_id="generation_node_limit",
        violated_invariant="node_count",
        reason=f"candidate has {len(draft.nodes)} nodes and exceeds configured max_nodes={max_nodes}",
    )
    return CompositionCandidate(
        **draft.model_dump(mode="python"),
        validity=CompositionValidity.REJECTED,
        rejection_reasons=(reason,),
    )


def generate_compositions(request: CompositionGenerationRequest) -> CompositionResult:
    """Deduplicate, validate, and emit a bounded reproducible candidate result."""

    if not isinstance(request, CompositionGenerationRequest):
        raise ValueError("request must be a CompositionGenerationRequest")
    unique: dict[str, CompositionCandidateDraft] = {}
    truncated = False
    for draft in iter_composition_candidate_drafts(request.instantiation_request):
        signature = semantic_candidate_signature(draft)
        if signature in unique:
            unique[signature] = merge_duplicate_drafts(unique[signature], draft)
            continue
        if len(unique) == request.policy.max_candidates:
            truncated = True
            break
        unique[signature] = draft

    valid_candidates: list[CompositionCandidate] = []
    rejected_candidates: list[CompositionCandidate] = []
    for draft in unique.values():
        if len(draft.nodes) > request.policy.max_nodes:
            rejected_candidates.append(
                _node_limit_candidate(draft, request.policy.max_nodes)
            )
            continue
        context = CompositionValidationContext(
            intelligence_result=request.instantiation_request.intelligence_result,
            graph=request.instantiation_request.graph,
            readiness_result=request.instantiation_request.readiness_result,
            registry=request.instantiation_request.registry,
            hard_requirement_ids=draft.satisfied_requirement_ids,
        )
        validation = validate_composition_candidate(draft, context)
        if validation.status is CompositionValidationStatus.PASS:
            valid_candidates.append(validation.candidate)
        else:
            rejected_candidates.append(validation.candidate)

    emitted = len(valid_candidates) + len(rejected_candidates)
    metadata = CompositionGenerationMetadata(
        max_nodes=request.policy.max_nodes,
        max_candidates=request.policy.max_candidates,
        emitted_valid_count=len(valid_candidates),
        emitted_rejected_count=len(rejected_candidates),
        enumeration_complete=not truncated,
        truncated=truncated,
        truncation_reason=(
            "first unique candidate beyond the configured cap was observed in canonical enumeration"
            if truncated
            else None
        ),
        candidate_count_lower_bound=(request.policy.max_candidates + 1 if truncated else emitted),
        canonical_order_description=(
            "certified pattern order followed by exact provider/model_id/family/revision order; canonical reproducibility only"
        ),
    )

    result_issues: tuple[CompositionRejection, ...] = ()
    if valid_candidates:
        status = CompositionResultStatus.READY
    elif not valid_candidates and not rejected_candidates and not request.instantiation_request.composition_required:
        status = CompositionResultStatus.NOT_APPLICABLE
    else:
        status = CompositionResultStatus.FAIL
        if not rejected_candidates:
            result_issues = (
                CompositionRejection(
                    issue_id="no_valid_composition",
                    violated_invariant="candidate_availability",
                    reason="composition is required but no valid candidate was generated",
                ),
            )
    return CompositionResult(
        status=status,
        valid_candidates=tuple(valid_candidates),
        rejected_candidates=tuple(rejected_candidates),
        generation_metadata=metadata,
        issues=result_issues,
    )
