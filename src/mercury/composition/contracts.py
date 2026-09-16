"""Immutable contracts for bounded logical model composition."""

from __future__ import annotations

import re
from enum import Enum
from typing import Any, Final, Literal, TypeVar

from pydantic import Field, StrictInt, field_validator, model_validator

from mercury.contracts.base import ContractModel
from mercury.graph.models import GraphDependencyType
from mercury.models.capabilities import ModelCapabilityRecord, ModelModality
from mercury.models.compatibility import ModelCapabilityRequirements
from mercury.models.evidence import CapabilityEvidenceAssessment


COMPOSITION_SCHEMA_VERSION: Final[Literal["mercury.model-composition/v1"]] = (
    "mercury.model-composition/v1"
)
MAX_COMPOSITION_NODES: Final[int] = 3
MAX_COMPOSITION_CANDIDATES: Final[int] = 256


class CompositionRole(str, Enum):
    PRIMARY = "primary"
    SPECIALIST = "specialist"
    VERIFIER = "verifier"
    CRITIC = "critic"
    RETRIEVAL_AUGMENTER = "retrieval_augmenter"
    TOOL_MODEL = "tool_model"


class CertifiedTopology(str, Enum):
    SINGLE = "single"
    PRIMARY_VERIFIER = "primary_verifier"
    PRIMARY_CRITIC = "primary_critic"
    PRIMARY_SPECIALIST_PRIMARY = "primary_specialist_primary"
    PRIMARY_RETRIEVAL_PRIMARY = "primary_retrieval_primary"
    PRIMARY_TOOL_PRIMARY = "primary_tool_primary"
    PRIMARY_SPECIALIST_VERIFIER = "primary_specialist_verifier"


class CompositionValidity(str, Enum):
    VALID = "valid"
    REJECTED = "rejected"


class CompositionResultStatus(str, Enum):
    READY = "ready"
    NOT_APPLICABLE = "not_applicable"
    FAIL = "fail"


_ContractValue = TypeVar("_ContractValue", bound=ContractModel)


def _nonblank(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be nonblank")
    return value


def _nonblank_tuple(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    if any(not isinstance(item, str) or not item.strip() for item in values):
        raise ValueError(f"{field_name} must contain nonblank values")
    return tuple(sorted(set(values)))


def _contract_tuple(
    values: tuple[_ContractValue, ...],
    expected_type: type[_ContractValue],
    key: Any,
    field_name: str,
    *,
    required: bool = False,
) -> tuple[_ContractValue, ...]:
    if any(not isinstance(item, expected_type) for item in values):
        raise ValueError(f"{field_name} must contain {expected_type.__name__} values")
    normalized = tuple(sorted({key(item): item for item in values}.values(), key=key))
    if required and not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return normalized


class CompositionProvenanceReference(ContractModel):
    source_phase: str
    artifact_id: str
    evidence: str

    @field_validator("source_phase", "artifact_id", "evidence")
    @classmethod
    def values_are_nonblank(cls, value: str) -> str:
        return _nonblank(value, "provenance value")


class CompositionArtifactContract(ContractModel):
    artifact_id: str
    modalities: tuple[ModelModality, ...]
    requires_structured_output: bool = False
    evidence: tuple[str, ...]

    @field_validator("artifact_id")
    @classmethod
    def artifact_id_is_nonblank(cls, value: str) -> str:
        return _nonblank(value, "artifact_id")

    @field_validator("modalities", mode="after")
    @classmethod
    def modalities_are_canonical(
        cls, values: tuple[ModelModality, ...]
    ) -> tuple[ModelModality, ...]:
        if any(not isinstance(item, ModelModality) for item in values):
            raise ValueError("modalities must contain ModelModality values")
        normalized = tuple(sorted(set(values), key=lambda item: item.value))
        if not normalized:
            raise ValueError("modalities must not be empty")
        return normalized

    @field_validator("evidence", mode="after")
    @classmethod
    def evidence_is_canonical(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        normalized = _nonblank_tuple(values, "artifact evidence")
        if not normalized:
            raise ValueError("artifact evidence must not be empty")
        return normalized


class CapabilityJustification(ContractModel):
    requirement_id: str
    capability_field: str
    declared_value: str
    reason: str

    @field_validator("requirement_id", "capability_field", "declared_value", "reason")
    @classmethod
    def values_are_nonblank(cls, value: str) -> str:
        return _nonblank(value, "capability justification value")


class CompositionNode(ContractModel):
    stage_id: str
    role: CompositionRole
    model_record: ModelCapabilityRecord
    requirements: ModelCapabilityRequirements
    input_artifacts: tuple[CompositionArtifactContract, ...]
    output_artifacts: tuple[CompositionArtifactContract, ...]
    justifications: tuple[CapabilityJustification, ...]
    provenance: tuple[CompositionProvenanceReference, ...]

    @field_validator("stage_id")
    @classmethod
    def stage_id_is_nonblank(cls, value: str) -> str:
        return _nonblank(value, "stage_id")

    @field_validator("input_artifacts", "output_artifacts", mode="after")
    @classmethod
    def artifacts_are_canonical(
        cls, values: tuple[CompositionArtifactContract, ...]
    ) -> tuple[CompositionArtifactContract, ...]:
        return _contract_tuple(
            values,
            CompositionArtifactContract,
            lambda item: item.artifact_id,
            "artifacts",
            required=True,
        )

    @field_validator("justifications", mode="after")
    @classmethod
    def justifications_are_canonical(
        cls, values: tuple[CapabilityJustification, ...]
    ) -> tuple[CapabilityJustification, ...]:
        return _contract_tuple(
            values,
            CapabilityJustification,
            lambda item: (
                item.requirement_id,
                item.capability_field,
                item.declared_value,
                item.reason,
            ),
            "justifications",
            required=True,
        )

    @field_validator("provenance", mode="after")
    @classmethod
    def provenance_is_canonical(
        cls, values: tuple[CompositionProvenanceReference, ...]
    ) -> tuple[CompositionProvenanceReference, ...]:
        return _contract_tuple(
            values,
            CompositionProvenanceReference,
            lambda item: (item.source_phase, item.artifact_id, item.evidence),
            "provenance",
            required=True,
        )


class CompositionEdge(ContractModel):
    source_stage_id: str
    target_stage_id: str
    dependency_type: GraphDependencyType
    artifact_id: str
    evidence: tuple[str, ...]

    @field_validator("source_stage_id", "target_stage_id", "artifact_id")
    @classmethod
    def identities_are_nonblank(cls, value: str) -> str:
        return _nonblank(value, "edge identity")

    @field_validator("evidence", mode="after")
    @classmethod
    def evidence_is_canonical(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        normalized = _nonblank_tuple(values, "edge evidence")
        if not normalized:
            raise ValueError("edge evidence must not be empty")
        return normalized


class CompositionCandidateDraft(ContractModel):
    schema_version: Literal["mercury.model-composition/v1"] = COMPOSITION_SCHEMA_VERSION
    composition_id: str
    request_id: str
    workload_id: str
    session_id: str
    graph_id: str
    pattern_id: str
    topology: CertifiedTopology
    nodes: tuple[CompositionNode, ...]
    edges: tuple[CompositionEdge, ...]
    satisfied_requirement_ids: tuple[str, ...]
    evidence_assessments: tuple[CapabilityEvidenceAssessment, ...] = ()
    provenance: tuple[CompositionProvenanceReference, ...]

    @field_validator(
        "composition_id", "request_id", "workload_id", "session_id", "graph_id", "pattern_id"
    )
    @classmethod
    def identities_are_nonblank(cls, value: str) -> str:
        return _nonblank(value, "composition identity")

    @field_validator("composition_id")
    @classmethod
    def composition_id_is_sha256(cls, value: str) -> str:
        if re.fullmatch(r"sha256:[0-9a-f]{64}", value) is None:
            raise ValueError("composition_id must be a deterministic lowercase sha256 identifier")
        return value

    @field_validator("nodes", mode="after")
    @classmethod
    def nodes_are_canonical(
        cls, values: tuple[CompositionNode, ...]
    ) -> tuple[CompositionNode, ...]:
        if not values:
            raise ValueError("nodes must not be empty")
        if len(values) > MAX_COMPOSITION_NODES:
            raise ValueError("composition exceeds MAX_COMPOSITION_NODES")
        if any(not isinstance(item, CompositionNode) for item in values):
            raise ValueError("nodes must contain CompositionNode values")
        stage_ids = tuple(item.stage_id for item in values)
        if len(stage_ids) != len(set(stage_ids)):
            raise ValueError("stage ids must be unique")
        return tuple(sorted(values, key=lambda item: item.stage_id))

    @field_validator("edges", mode="after")
    @classmethod
    def edges_are_canonical(
        cls, values: tuple[CompositionEdge, ...]
    ) -> tuple[CompositionEdge, ...]:
        return _contract_tuple(
            values,
            CompositionEdge,
            lambda item: (
                item.source_stage_id,
                item.target_stage_id,
                item.dependency_type.value,
                item.artifact_id,
                item.evidence,
            ),
            "edges",
        )

    @field_validator("satisfied_requirement_ids", mode="after")
    @classmethod
    def requirements_are_canonical(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        normalized = _nonblank_tuple(values, "satisfied requirement ids")
        if not normalized:
            raise ValueError("satisfied_requirement_ids must not be empty")
        return normalized

    @field_validator("evidence_assessments", mode="after")
    @classmethod
    def assessments_are_canonical(
        cls, values: tuple[CapabilityEvidenceAssessment, ...]
    ) -> tuple[CapabilityEvidenceAssessment, ...]:
        if any(not isinstance(item, CapabilityEvidenceAssessment) for item in values):
            raise ValueError("evidence_assessments must contain CapabilityEvidenceAssessment values")
        return tuple(
            sorted(
                {item.model_dump_json(): item for item in values}.values(),
                key=lambda item: item.model_dump_json(),
            )
        )

    @field_validator("provenance", mode="after")
    @classmethod
    def provenance_is_canonical(
        cls, values: tuple[CompositionProvenanceReference, ...]
    ) -> tuple[CompositionProvenanceReference, ...]:
        return _contract_tuple(
            values,
            CompositionProvenanceReference,
            lambda item: (item.source_phase, item.artifact_id, item.evidence),
            "provenance",
            required=True,
        )

    @model_validator(mode="after")
    def graph_is_a_connected_dag(self) -> CompositionCandidateDraft:
        node_ids = {item.stage_id for item in self.nodes}
        incoming = {node_id: 0 for node_id in node_ids}
        outgoing = {node_id: [] for node_id in node_ids}
        undirected = {node_id: set() for node_id in node_ids}
        for edge in self.edges:
            if edge.source_stage_id not in node_ids or edge.target_stage_id not in node_ids:
                raise ValueError("edge references must identify existing stages")
            if edge.source_stage_id == edge.target_stage_id:
                raise ValueError("composition self-edges are not allowed")
            incoming[edge.target_stage_id] += 1
            outgoing[edge.source_stage_id].append(edge.target_stage_id)
            undirected[edge.source_stage_id].add(edge.target_stage_id)
            undirected[edge.target_stage_id].add(edge.source_stage_id)

        if len(node_ids) > 1:
            if any(not neighbors for neighbors in undirected.values()):
                raise ValueError("composition contains an orphan stage")
            seen: set[str] = set()
            pending = [min(node_ids)]
            while pending:
                current = pending.pop()
                if current in seen:
                    continue
                seen.add(current)
                pending.extend(sorted(undirected[current] - seen, reverse=True))
            if seen != node_ids:
                raise ValueError("composition stages must form one connected graph")

        ready = sorted(node_id for node_id, count in incoming.items() if count == 0)
        visited = 0
        while ready:
            current = ready.pop(0)
            visited += 1
            for target in sorted(outgoing[current]):
                incoming[target] -= 1
                if incoming[target] == 0:
                    ready.append(target)
                    ready.sort()
        if visited != len(node_ids):
            raise ValueError("composition must be acyclic")
        return self


class CompositionRejection(ContractModel):
    issue_id: str
    stage_id: str | None = None
    edge_reference: str | None = None
    violated_invariant: str
    reason: str

    @field_validator("issue_id", "violated_invariant", "reason")
    @classmethod
    def required_values_are_nonblank(cls, value: str) -> str:
        return _nonblank(value, "rejection value")

    @field_validator("stage_id", "edge_reference")
    @classmethod
    def optional_values_are_nonblank(cls, value: str | None) -> str | None:
        return None if value is None else _nonblank(value, "rejection reference")


class CompositionCandidate(CompositionCandidateDraft):
    validity: CompositionValidity
    rejection_reasons: tuple[CompositionRejection, ...]

    @field_validator("rejection_reasons", mode="after")
    @classmethod
    def rejections_are_canonical(
        cls, values: tuple[CompositionRejection, ...]
    ) -> tuple[CompositionRejection, ...]:
        return _contract_tuple(
            values,
            CompositionRejection,
            lambda item: (
                item.issue_id,
                item.stage_id or "",
                item.edge_reference or "",
                item.violated_invariant,
                item.reason,
            ),
            "rejection_reasons",
        )

    @model_validator(mode="after")
    def validity_matches_rejections(self) -> CompositionCandidate:
        if self.validity is CompositionValidity.VALID and self.rejection_reasons:
            raise ValueError("VALID candidates must not contain rejection reasons")
        if self.validity is CompositionValidity.REJECTED and not self.rejection_reasons:
            raise ValueError("REJECTED candidates require a rejection reason")
        return self


class CompositionGenerationPolicy(ContractModel):
    max_nodes: StrictInt = Field(default=MAX_COMPOSITION_NODES, ge=1, le=MAX_COMPOSITION_NODES)
    max_candidates: StrictInt = Field(
        default=MAX_COMPOSITION_CANDIDATES, ge=1, le=MAX_COMPOSITION_CANDIDATES
    )


class CompositionGenerationMetadata(ContractModel):
    max_nodes: StrictInt = Field(ge=1, le=MAX_COMPOSITION_NODES)
    max_candidates: StrictInt = Field(ge=1, le=MAX_COMPOSITION_CANDIDATES)
    emitted_valid_count: StrictInt = Field(ge=0)
    emitted_rejected_count: StrictInt = Field(ge=0)
    enumeration_complete: bool
    truncated: bool
    truncation_reason: str | None = None
    candidate_count_lower_bound: StrictInt = Field(ge=0)
    canonical_order_description: str

    @field_validator("canonical_order_description")
    @classmethod
    def ordering_description_is_nonblank(cls, value: str) -> str:
        return _nonblank(value, "canonical_order_description")

    @field_validator("truncation_reason")
    @classmethod
    def truncation_reason_is_nonblank_when_present(
        cls, value: str | None
    ) -> str | None:
        return None if value is None else _nonblank(value, "truncation_reason")

    @model_validator(mode="after")
    def metadata_is_consistent(self) -> CompositionGenerationMetadata:
        emitted = self.emitted_valid_count + self.emitted_rejected_count
        if emitted > self.max_candidates:
            raise ValueError("emitted candidates exceed max_candidates")
        if self.truncated:
            if self.enumeration_complete:
                raise ValueError("truncated enumeration cannot be complete")
            if self.truncation_reason is None:
                raise ValueError("truncated enumeration requires a reason")
            if self.candidate_count_lower_bound <= self.max_candidates:
                raise ValueError("truncation requires a lower bound above max_candidates")
        else:
            if not self.enumeration_complete:
                raise ValueError("non-truncated enumeration must be complete")
            if self.truncation_reason is not None:
                raise ValueError("non-truncated enumeration cannot have a truncation reason")
            if self.candidate_count_lower_bound != emitted:
                raise ValueError("complete enumeration lower bound must equal emitted count")
        return self


class CompositionResult(ContractModel):
    status: CompositionResultStatus
    valid_candidates: tuple[CompositionCandidate, ...]
    rejected_candidates: tuple[CompositionCandidate, ...]
    generation_metadata: CompositionGenerationMetadata
    issues: tuple[CompositionRejection, ...] = ()

    @field_validator("valid_candidates", "rejected_candidates", mode="after")
    @classmethod
    def candidates_are_canonical(
        cls, values: tuple[CompositionCandidate, ...]
    ) -> tuple[CompositionCandidate, ...]:
        if any(type(item) is not CompositionCandidate for item in values):
            raise ValueError("final results may contain only validated CompositionCandidate values")
        ids = tuple(item.composition_id for item in values)
        if len(ids) != len(set(ids)):
            raise ValueError("candidate composition ids must be unique")
        return tuple(sorted(values, key=lambda item: item.composition_id))

    @field_validator("issues", mode="after")
    @classmethod
    def issues_are_canonical(
        cls, values: tuple[CompositionRejection, ...]
    ) -> tuple[CompositionRejection, ...]:
        return CompositionCandidate.rejections_are_canonical(values)

    @model_validator(mode="after")
    def result_is_consistent(self) -> CompositionResult:
        if any(item.validity is not CompositionValidity.VALID for item in self.valid_candidates):
            raise ValueError("valid_candidates must contain only VALID candidates")
        if any(
            item.validity is not CompositionValidity.REJECTED
            for item in self.rejected_candidates
        ):
            raise ValueError("rejected_candidates must contain only REJECTED candidates")
        all_ids = tuple(
            item.composition_id
            for item in self.valid_candidates + self.rejected_candidates
        )
        if len(all_ids) != len(set(all_ids)):
            raise ValueError("candidate ids must be unique across the result")
        if self.generation_metadata.emitted_valid_count != len(self.valid_candidates):
            raise ValueError("valid candidate count does not match generation metadata")
        if self.generation_metadata.emitted_rejected_count != len(self.rejected_candidates):
            raise ValueError("rejected candidate count does not match generation metadata")

        if self.status is CompositionResultStatus.READY:
            if not self.valid_candidates:
                raise ValueError("READY requires at least one valid candidate")
        elif self.status is CompositionResultStatus.NOT_APPLICABLE:
            if self.valid_candidates or self.rejected_candidates or self.issues:
                raise ValueError("NOT_APPLICABLE must contain no candidates or issues")
        elif self.status is CompositionResultStatus.FAIL:
            if self.valid_candidates:
                raise ValueError("FAIL cannot contain valid candidates")
            if not self.rejected_candidates and not self.issues:
                raise ValueError("FAIL requires an explicit rejection or issue")
        return self


def canonical_model_identity(
    record: ModelCapabilityRecord,
) -> tuple[str, str, str, str]:
    """Return the exact provider/family/model/revision identity without inference."""

    if not isinstance(record, ModelCapabilityRecord):
        raise ValueError("record must be a ModelCapabilityRecord")
    return record.provider, record.family, record.model_id, record.revision
