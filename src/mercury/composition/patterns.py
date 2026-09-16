"""Certified bounded topology definitions for logical model composition."""

from __future__ import annotations

from enum import Enum
from typing import Final

from pydantic import Field, StrictInt, field_validator, model_validator

from mercury.composition.contracts import (
    MAX_COMPOSITION_NODES,
    CertifiedTopology,
    CompositionRole,
)
from mercury.contracts.base import ContractModel
from mercury.graph.models import GraphDependencyType


class PatternApplicability(str, Enum):
    SINGLE_CAPABLE = "single_capable"
    VERIFICATION_REQUIRED = "verification_required"
    CRITIQUE_REQUIRED = "critique_required"
    SPECIALIST_RETURN_REQUIRED = "specialist_return_required"
    RETRIEVAL_RETURN_REQUIRED = "retrieval_return_required"
    TOOL_RETURN_REQUIRED = "tool_return_required"
    SPECIALIST_VERIFICATION_REQUIRED = "specialist_verification_required"


def _nonblank(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be nonblank")
    return value


class PatternSlot(ContractModel):
    stage_id: str
    role: CompositionRole
    identity_group: str | None = None

    @field_validator("stage_id")
    @classmethod
    def stage_id_is_nonblank(cls, value: str) -> str:
        return _nonblank(value, "stage_id")

    @field_validator("identity_group")
    @classmethod
    def identity_group_is_nonblank_when_present(
        cls, value: str | None
    ) -> str | None:
        return None if value is None else _nonblank(value, "identity_group")


class PatternEdge(ContractModel):
    source_stage_id: str
    target_stage_id: str
    dependency_type: GraphDependencyType

    @field_validator("source_stage_id", "target_stage_id")
    @classmethod
    def stage_ids_are_nonblank(cls, value: str) -> str:
        return _nonblank(value, "edge stage id")

    @model_validator(mode="after")
    def edge_is_not_self_referential(self) -> PatternEdge:
        if self.source_stage_id == self.target_stage_id:
            raise ValueError("pattern self-edges are not allowed")
        return self


_ROLE_SEQUENCES: Final[dict[CertifiedTopology, tuple[CompositionRole, ...]]] = {
    CertifiedTopology.SINGLE: (CompositionRole.PRIMARY,),
    CertifiedTopology.PRIMARY_VERIFIER: (
        CompositionRole.PRIMARY,
        CompositionRole.VERIFIER,
    ),
    CertifiedTopology.PRIMARY_CRITIC: (
        CompositionRole.PRIMARY,
        CompositionRole.CRITIC,
    ),
    CertifiedTopology.PRIMARY_SPECIALIST_PRIMARY: (
        CompositionRole.PRIMARY,
        CompositionRole.SPECIALIST,
        CompositionRole.PRIMARY,
    ),
    CertifiedTopology.PRIMARY_RETRIEVAL_PRIMARY: (
        CompositionRole.PRIMARY,
        CompositionRole.RETRIEVAL_AUGMENTER,
        CompositionRole.PRIMARY,
    ),
    CertifiedTopology.PRIMARY_TOOL_PRIMARY: (
        CompositionRole.PRIMARY,
        CompositionRole.TOOL_MODEL,
        CompositionRole.PRIMARY,
    ),
    CertifiedTopology.PRIMARY_SPECIALIST_VERIFIER: (
        CompositionRole.PRIMARY,
        CompositionRole.SPECIALIST,
        CompositionRole.VERIFIER,
    ),
}

_APPLICABILITY: Final[dict[CertifiedTopology, PatternApplicability]] = {
    CertifiedTopology.SINGLE: PatternApplicability.SINGLE_CAPABLE,
    CertifiedTopology.PRIMARY_VERIFIER: PatternApplicability.VERIFICATION_REQUIRED,
    CertifiedTopology.PRIMARY_CRITIC: PatternApplicability.CRITIQUE_REQUIRED,
    CertifiedTopology.PRIMARY_SPECIALIST_PRIMARY: (
        PatternApplicability.SPECIALIST_RETURN_REQUIRED
    ),
    CertifiedTopology.PRIMARY_RETRIEVAL_PRIMARY: (
        PatternApplicability.RETRIEVAL_RETURN_REQUIRED
    ),
    CertifiedTopology.PRIMARY_TOOL_PRIMARY: PatternApplicability.TOOL_RETURN_REQUIRED,
    CertifiedTopology.PRIMARY_SPECIALIST_VERIFIER: (
        PatternApplicability.SPECIALIST_VERIFICATION_REQUIRED
    ),
}

_PATTERN_IDS: Final[dict[CertifiedTopology, str]] = {
    topology: f"pattern-{topology.value.replace('_', '-')}-v1"
    for topology in CertifiedTopology
}

_ALLOWED_TRANSITIONS: Final[
    frozenset[tuple[CompositionRole, CompositionRole]]
] = frozenset(
    {
        (CompositionRole.PRIMARY, CompositionRole.VERIFIER),
        (CompositionRole.PRIMARY, CompositionRole.CRITIC),
        (CompositionRole.PRIMARY, CompositionRole.SPECIALIST),
        (CompositionRole.PRIMARY, CompositionRole.RETRIEVAL_AUGMENTER),
        (CompositionRole.PRIMARY, CompositionRole.TOOL_MODEL),
        (CompositionRole.SPECIALIST, CompositionRole.PRIMARY),
        (CompositionRole.SPECIALIST, CompositionRole.VERIFIER),
        (CompositionRole.RETRIEVAL_AUGMENTER, CompositionRole.PRIMARY),
        (CompositionRole.TOOL_MODEL, CompositionRole.PRIMARY),
    }
)

_RETURN_TOPOLOGIES: Final[frozenset[CertifiedTopology]] = frozenset(
    {
        CertifiedTopology.PRIMARY_SPECIALIST_PRIMARY,
        CertifiedTopology.PRIMARY_RETRIEVAL_PRIMARY,
        CertifiedTopology.PRIMARY_TOOL_PRIMARY,
    }
)


class CertifiedCompositionPattern(ContractModel):
    topology: CertifiedTopology
    pattern_id: str
    applicability: PatternApplicability
    slots: tuple[PatternSlot, ...]
    edges: tuple[PatternEdge, ...]
    max_nodes: StrictInt = Field(ge=1, le=MAX_COMPOSITION_NODES)

    @field_validator("pattern_id")
    @classmethod
    def pattern_id_is_nonblank(cls, value: str) -> str:
        return _nonblank(value, "pattern_id")

    @field_validator("slots", mode="after")
    @classmethod
    def slots_are_valid(cls, values: tuple[PatternSlot, ...]) -> tuple[PatternSlot, ...]:
        if not values:
            raise ValueError("pattern slots must not be empty")
        if len(values) > MAX_COMPOSITION_NODES:
            raise ValueError("pattern exceeds MAX_COMPOSITION_NODES")
        if any(not isinstance(item, PatternSlot) for item in values):
            raise ValueError("slots must contain PatternSlot values")
        stage_ids = tuple(item.stage_id for item in values)
        if len(stage_ids) != len(set(stage_ids)):
            raise ValueError("pattern stage ids must be unique")
        return values

    @field_validator("edges", mode="after")
    @classmethod
    def edges_are_canonical(cls, values: tuple[PatternEdge, ...]) -> tuple[PatternEdge, ...]:
        if any(not isinstance(item, PatternEdge) for item in values):
            raise ValueError("edges must contain PatternEdge values")
        keyed = {
            (item.source_stage_id, item.target_stage_id, item.dependency_type.value): item
            for item in values
        }
        return tuple(keyed[key] for key in sorted(keyed))

    @model_validator(mode="after")
    def pattern_matches_certified_shape(self) -> CertifiedCompositionPattern:
        expected_roles = _ROLE_SEQUENCES[self.topology]
        if self.pattern_id != _PATTERN_IDS[self.topology]:
            raise ValueError("pattern_id must match the certified topology")
        if self.applicability is not _APPLICABILITY[self.topology]:
            raise ValueError("applicability must match the certified topology")
        if self.max_nodes != len(expected_roles) or len(self.slots) != self.max_nodes:
            raise ValueError("slot count and max_nodes must match the certified topology")

        slots_by_id = {item.stage_id: item for item in self.slots}
        node_ids = set(slots_by_id)
        incoming = {node_id: 0 for node_id in node_ids}
        outgoing = {node_id: [] for node_id in node_ids}
        undirected = {node_id: set() for node_id in node_ids}

        for edge in self.edges:
            if edge.source_stage_id not in node_ids or edge.target_stage_id not in node_ids:
                raise ValueError("pattern edges must reference declared stages")
            if edge.dependency_type is not GraphDependencyType.DATA:
                raise ValueError("certified pattern handoffs must use DATA dependencies")
            source_role = slots_by_id[edge.source_stage_id].role
            target_role = slots_by_id[edge.target_stage_id].role
            if (source_role, target_role) not in _ALLOWED_TRANSITIONS:
                raise ValueError("pattern contains an undeclared role transition")
            incoming[edge.target_stage_id] += 1
            outgoing[edge.source_stage_id].append(edge.target_stage_id)
            undirected[edge.source_stage_id].add(edge.target_stage_id)
            undirected[edge.target_stage_id].add(edge.source_stage_id)

        if len(node_ids) > 1:
            if any(not neighbors for neighbors in undirected.values()):
                raise ValueError("pattern contains an orphan stage")
            seen: set[str] = set()
            pending = [min(node_ids)]
            while pending:
                current = pending.pop()
                if current in seen:
                    continue
                seen.add(current)
                pending.extend(sorted(undirected[current] - seen, reverse=True))
            if seen != node_ids:
                raise ValueError("pattern must be connected")

        ready = sorted(node_id for node_id, count in incoming.items() if count == 0)
        ordered_ids: list[str] = []
        while ready:
            current = ready.pop(0)
            ordered_ids.append(current)
            for target in sorted(outgoing[current]):
                incoming[target] -= 1
                if incoming[target] == 0:
                    ready.append(target)
                    ready.sort()
        if len(ordered_ids) != len(node_ids):
            raise ValueError("certified patterns must be acyclic")

        ordered_slots = tuple(slots_by_id[stage_id] for stage_id in ordered_ids)
        if tuple(item.role for item in ordered_slots) != expected_roles:
            raise ValueError("roles and transitions must match the certified topology")
        if len(self.edges) != max(0, len(self.slots) - 1):
            raise ValueError("certified topology must be one bounded logical path")

        if self.topology in _RETURN_TOPOLOGIES:
            primary_slots = tuple(
                item for item in ordered_slots if item.role is CompositionRole.PRIMARY
            )
            if tuple(item.identity_group for item in primary_slots) != (
                "primary",
                "primary",
            ):
                raise ValueError(
                    "return topology PRIMARY stages require identity_group='primary'"
                )
        elif any(item.identity_group is not None for item in ordered_slots):
            raise ValueError("identity groups are only certified for return topology PRIMARY stages")

        object.__setattr__(self, "slots", ordered_slots)
        return self


def _slot(
    stage_id: str,
    role: CompositionRole,
    identity_group: str | None = None,
) -> PatternSlot:
    return PatternSlot(stage_id=stage_id, role=role, identity_group=identity_group)


def _edge(source: str, target: str) -> PatternEdge:
    return PatternEdge(
        source_stage_id=source,
        target_stage_id=target,
        dependency_type=GraphDependencyType.DATA,
    )


CERTIFIED_PATTERNS: Final[tuple[CertifiedCompositionPattern, ...]] = (
    CertifiedCompositionPattern(
        topology=CertifiedTopology.SINGLE,
        pattern_id="pattern-single-v1",
        applicability=PatternApplicability.SINGLE_CAPABLE,
        slots=(_slot("primary", CompositionRole.PRIMARY),),
        edges=(),
        max_nodes=1,
    ),
    CertifiedCompositionPattern(
        topology=CertifiedTopology.PRIMARY_VERIFIER,
        pattern_id="pattern-primary-verifier-v1",
        applicability=PatternApplicability.VERIFICATION_REQUIRED,
        slots=(
            _slot("primary", CompositionRole.PRIMARY),
            _slot("verifier", CompositionRole.VERIFIER),
        ),
        edges=(_edge("primary", "verifier"),),
        max_nodes=2,
    ),
    CertifiedCompositionPattern(
        topology=CertifiedTopology.PRIMARY_CRITIC,
        pattern_id="pattern-primary-critic-v1",
        applicability=PatternApplicability.CRITIQUE_REQUIRED,
        slots=(
            _slot("primary", CompositionRole.PRIMARY),
            _slot("critic", CompositionRole.CRITIC),
        ),
        edges=(_edge("primary", "critic"),),
        max_nodes=2,
    ),
    CertifiedCompositionPattern(
        topology=CertifiedTopology.PRIMARY_SPECIALIST_PRIMARY,
        pattern_id="pattern-primary-specialist-primary-v1",
        applicability=PatternApplicability.SPECIALIST_RETURN_REQUIRED,
        slots=(
            _slot("primary-in", CompositionRole.PRIMARY, "primary"),
            _slot("specialist", CompositionRole.SPECIALIST),
            _slot("primary-out", CompositionRole.PRIMARY, "primary"),
        ),
        edges=(
            _edge("primary-in", "specialist"),
            _edge("specialist", "primary-out"),
        ),
        max_nodes=3,
    ),
    CertifiedCompositionPattern(
        topology=CertifiedTopology.PRIMARY_RETRIEVAL_PRIMARY,
        pattern_id="pattern-primary-retrieval-primary-v1",
        applicability=PatternApplicability.RETRIEVAL_RETURN_REQUIRED,
        slots=(
            _slot("primary-in", CompositionRole.PRIMARY, "primary"),
            _slot("retrieval-augmenter", CompositionRole.RETRIEVAL_AUGMENTER),
            _slot("primary-out", CompositionRole.PRIMARY, "primary"),
        ),
        edges=(
            _edge("primary-in", "retrieval-augmenter"),
            _edge("retrieval-augmenter", "primary-out"),
        ),
        max_nodes=3,
    ),
    CertifiedCompositionPattern(
        topology=CertifiedTopology.PRIMARY_TOOL_PRIMARY,
        pattern_id="pattern-primary-tool-primary-v1",
        applicability=PatternApplicability.TOOL_RETURN_REQUIRED,
        slots=(
            _slot("primary-in", CompositionRole.PRIMARY, "primary"),
            _slot("tool-model", CompositionRole.TOOL_MODEL),
            _slot("primary-out", CompositionRole.PRIMARY, "primary"),
        ),
        edges=(
            _edge("primary-in", "tool-model"),
            _edge("tool-model", "primary-out"),
        ),
        max_nodes=3,
    ),
    CertifiedCompositionPattern(
        topology=CertifiedTopology.PRIMARY_SPECIALIST_VERIFIER,
        pattern_id="pattern-primary-specialist-verifier-v1",
        applicability=PatternApplicability.SPECIALIST_VERIFICATION_REQUIRED,
        slots=(
            _slot("primary", CompositionRole.PRIMARY),
            _slot("specialist", CompositionRole.SPECIALIST),
            _slot("verifier", CompositionRole.VERIFIER),
        ),
        edges=(
            _edge("primary", "specialist"),
            _edge("specialist", "verifier"),
        ),
        max_nodes=3,
    ),
)

_PATTERNS_BY_TOPOLOGY: Final[dict[CertifiedTopology, CertifiedCompositionPattern]] = {
    item.topology: item for item in CERTIFIED_PATTERNS
}


def get_certified_patterns() -> tuple[CertifiedCompositionPattern, ...]:
    """Return the seven patterns in enum declaration order, never preference order."""

    return CERTIFIED_PATTERNS


def get_certified_pattern(topology: CertifiedTopology) -> CertifiedCompositionPattern:
    """Return the exact certified pattern for a topology."""

    if not isinstance(topology, CertifiedTopology):
        raise ValueError("topology must be a CertifiedTopology")
    return _PATTERNS_BY_TOPOLOGY[topology]
