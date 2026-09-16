from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from mercury.composition.contracts import (
    MAX_COMPOSITION_NODES,
    CertifiedTopology,
    CompositionRole,
)
from mercury.composition.patterns import (
    CERTIFIED_PATTERNS,
    CertifiedCompositionPattern,
    PatternApplicability,
    PatternEdge,
    PatternSlot,
    get_certified_pattern,
    get_certified_patterns,
)
from mercury.graph.models import GraphDependencyType


EXPECTED_SHAPES = {
    CertifiedTopology.SINGLE: (
        (CompositionRole.PRIMARY,),
        (),
    ),
    CertifiedTopology.PRIMARY_VERIFIER: (
        (CompositionRole.PRIMARY, CompositionRole.VERIFIER),
        (("primary", "verifier"),),
    ),
    CertifiedTopology.PRIMARY_CRITIC: (
        (CompositionRole.PRIMARY, CompositionRole.CRITIC),
        (("primary", "critic"),),
    ),
    CertifiedTopology.PRIMARY_SPECIALIST_PRIMARY: (
        (CompositionRole.PRIMARY, CompositionRole.SPECIALIST, CompositionRole.PRIMARY),
        (("primary-in", "specialist"), ("specialist", "primary-out")),
    ),
    CertifiedTopology.PRIMARY_RETRIEVAL_PRIMARY: (
        (
            CompositionRole.PRIMARY,
            CompositionRole.RETRIEVAL_AUGMENTER,
            CompositionRole.PRIMARY,
        ),
        (
            ("primary-in", "retrieval-augmenter"),
            ("retrieval-augmenter", "primary-out"),
        ),
    ),
    CertifiedTopology.PRIMARY_TOOL_PRIMARY: (
        (CompositionRole.PRIMARY, CompositionRole.TOOL_MODEL, CompositionRole.PRIMARY),
        (("primary-in", "tool-model"), ("tool-model", "primary-out")),
    ),
    CertifiedTopology.PRIMARY_SPECIALIST_VERIFIER: (
        (CompositionRole.PRIMARY, CompositionRole.SPECIALIST, CompositionRole.VERIFIER),
        (("primary", "specialist"), ("specialist", "verifier")),
    ),
}


def slot(
    stage_id: str,
    role: CompositionRole,
    identity_group: str | None = None,
) -> PatternSlot:
    return PatternSlot(
        stage_id=stage_id, role=role, identity_group=identity_group
    )


def edge(source: str, target: str) -> PatternEdge:
    return PatternEdge(
        source_stage_id=source,
        target_stage_id=target,
        dependency_type=GraphDependencyType.DATA,
    )


def pattern(**changes: Any) -> CertifiedCompositionPattern:
    values: dict[str, Any] = {
        "topology": CertifiedTopology.PRIMARY_VERIFIER,
        "pattern_id": "pattern-primary-verifier-v1",
        "applicability": PatternApplicability.VERIFICATION_REQUIRED,
        "slots": (
            slot("primary", CompositionRole.PRIMARY),
            slot("verifier", CompositionRole.VERIFIER),
        ),
        "edges": (edge("primary", "verifier"),),
        "max_nodes": 2,
    }
    values.update(changes)
    return CertifiedCompositionPattern(**values)


def test_certified_library_contains_exactly_seven_locked_shapes() -> None:
    patterns = get_certified_patterns()

    assert tuple(item.topology for item in patterns) == tuple(CertifiedTopology)
    assert len(patterns) == 7
    assert all(len(item.slots) <= MAX_COMPOSITION_NODES for item in patterns)


@pytest.mark.parametrize("topology", tuple(CertifiedTopology))
def test_each_certified_pattern_has_exact_role_sequence_and_edges(
    topology: CertifiedTopology,
) -> None:
    value = get_certified_pattern(topology)
    expected_roles, expected_edges = EXPECTED_SHAPES[topology]

    assert tuple(item.role for item in value.slots) == expected_roles
    assert tuple(
        (item.source_stage_id, item.target_stage_id) for item in value.edges
    ) == expected_edges
    assert all(
        item.dependency_type is GraphDependencyType.DATA for item in value.edges
    )


def test_single_is_one_primary_without_edges() -> None:
    value = get_certified_pattern(CertifiedTopology.SINGLE)

    assert tuple((item.stage_id, item.role) for item in value.slots) == (
        ("primary", CompositionRole.PRIMARY),
    )
    assert value.edges == ()


@pytest.mark.parametrize(
    "topology",
    (
        CertifiedTopology.PRIMARY_SPECIALIST_PRIMARY,
        CertifiedTopology.PRIMARY_RETRIEVAL_PRIMARY,
        CertifiedTopology.PRIMARY_TOOL_PRIMARY,
    ),
)
def test_return_topologies_require_same_exact_primary_identity_group(
    topology: CertifiedTopology,
) -> None:
    primary_slots = tuple(
        item
        for item in get_certified_pattern(topology).slots
        if item.role is CompositionRole.PRIMARY
    )

    assert tuple(item.stage_id for item in primary_slots) == (
        "primary-in", "primary-out"
    )
    assert tuple(item.identity_group for item in primary_slots) == (
        "primary", "primary"
    )


def test_library_and_lookup_are_deterministic_and_immutable() -> None:
    first = get_certified_patterns()
    second = get_certified_patterns()

    assert first is CERTIFIED_PATTERNS
    assert first == second
    assert tuple(item.model_dump_json() for item in first) == tuple(
        item.model_dump_json() for item in second
    )
    with pytest.raises(TypeError):
        first[0] = first[1]  # type: ignore[index]
    with pytest.raises(ValidationError):
        first[0].topology = CertifiedTopology.PRIMARY_VERIFIER  # type: ignore[misc]


def test_equivalent_definition_normalizes_to_topological_order() -> None:
    canonical = pattern()
    reordered = pattern(
        slots=tuple(reversed(canonical.slots)),
        edges=tuple(reversed(canonical.edges)),
    )

    assert reordered == canonical
    assert reordered.model_dump_json() == canonical.model_dump_json()


@pytest.mark.parametrize(
    "changes",
    (
        {
            "slots": (
                slot("primary", CompositionRole.PRIMARY),
                slot("primary", CompositionRole.VERIFIER),
            )
        },
        {"edges": (edge("primary", "missing"),)},
        {
            "slots": (
                slot("primary", CompositionRole.PRIMARY),
                slot("verifier", CompositionRole.VERIFIER),
            ),
            "edges": (edge("primary", "verifier"), edge("verifier", "primary")),
        },
        {
            "slots": (
                slot("primary", CompositionRole.PRIMARY),
                slot("verifier", CompositionRole.VERIFIER),
                slot("orphan", CompositionRole.CRITIC),
            ),
            "max_nodes": 3,
        },
    ),
)
def test_malformed_graph_shapes_are_rejected(changes: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        pattern(**changes)


def test_more_than_three_slots_is_rejected() -> None:
    with pytest.raises(ValidationError):
        pattern(
            slots=(
                slot("primary", CompositionRole.PRIMARY),
                slot("specialist", CompositionRole.SPECIALIST),
                slot("verifier", CompositionRole.VERIFIER),
                slot("critic", CompositionRole.CRITIC),
            ),
            edges=(
                edge("primary", "specialist"),
                edge("specialist", "verifier"),
                edge("verifier", "critic"),
            ),
            max_nodes=4,
        )


def test_self_edge_is_rejected() -> None:
    with pytest.raises(ValidationError):
        edge("primary", "primary")


def test_unknown_role_and_unsupported_topology_are_rejected() -> None:
    with pytest.raises(ValidationError):
        PatternSlot(stage_id="unknown", role="router")
    with pytest.raises(ValidationError):
        pattern(topology="primary_judge")
    with pytest.raises(ValueError):
        get_certified_pattern("primary_judge")  # type: ignore[arg-type]


def test_undeclared_role_transition_is_rejected() -> None:
    with pytest.raises(ValidationError):
        pattern(
            slots=(
                slot("critic", CompositionRole.CRITIC),
                slot("primary", CompositionRole.PRIMARY),
            ),
            edges=(edge("critic", "primary"),),
        )


def test_certified_label_cannot_hide_a_different_valid_shape() -> None:
    with pytest.raises(ValidationError):
        pattern(
            slots=(
                slot("primary", CompositionRole.PRIMARY),
                slot("critic", CompositionRole.CRITIC),
            ),
            edges=(edge("primary", "critic"),),
        )


def test_patterns_do_not_bind_models_or_expose_execution_decisions() -> None:
    forbidden = {
        "model", "model_id", "provider", "rank", "score", "winner",
        "hardware", "device", "placement", "region", "scheduler", "runtime",
    }
    for contract_type in (PatternSlot, PatternEdge, CertifiedCompositionPattern):
        assert forbidden.isdisjoint(contract_type.model_fields)
