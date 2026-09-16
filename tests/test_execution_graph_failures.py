from dataclasses import replace

import pytest

from mercury.graph.models import ExecutionGraph, ExecutionGraphEdge, ExecutionGraphNode, GraphDependencyType, GraphNodeType
from mercury.graph.readiness import GraphReadinessStatus, evaluate_graph_readiness
from mercury.graph.transformation import transform_execution_graph
from mercury.graph.validation import GraphValidationStatus, validate_execution_graph
from mercury.intelligence.models import ComputationalCapability, Evidence


def node(node_id, node_type=GraphNodeType.TRANSFORM, capability=ComputationalCapability.GENERATION):
    return ExecutionGraphNode(node_id, node_type, f"logical {node_type.value}", [capability], [Evidence("phase2", "explicit evidence")])


def edge(source, target, kind=GraphDependencyType.DATA):
    return ExecutionGraphEdge(source, target, kind, [Evidence("graph", "logical dependency")])


def graph(nodes=None, edges=None, **identity):
    nodes = nodes or [node("input", GraphNodeType.INPUT), node("transform"), node("output", GraphNodeType.OUTPUT)]
    edges = edges if edges is not None else [edge("input", "transform"), edge("transform", "output")]
    return ExecutionGraph(identity.get("graph_id", "graph-1"), identity.get("request_id", "request-1"), identity.get("workload_id", "workload-1"), identity.get("session_id", "session-1"), nodes, edges, [Evidence("phase2", "graph provenance")])


@pytest.mark.parametrize("field", ["graph_id", "request_id", "workload_id", "session_id"])
def test_blank_graph_identity_is_rejected(field: str) -> None:
    with pytest.raises(ValueError, match=field):
        graph(**{field: " "})


def test_duplicate_dangling_and_cycles_are_rejected_or_fail_validation() -> None:
    with pytest.raises(ValueError, match="unique"):
        graph(nodes=[node("input", GraphNodeType.INPUT), node("input", GraphNodeType.OUTPUT)])
    with pytest.raises(ValueError, match="source"):
        graph(edges=[edge("missing", "output")])
    escaped = graph()
    object.__setattr__(escaped, "edges", (edge("input", "transform"), edge("transform", "output"), edge("output", "input")))
    assert validate_execution_graph(escaped).status is GraphValidationStatus.FAIL


def test_disconnected_orphan_and_entry_exit_attacks_fail_validation() -> None:
    invalid = graph(nodes=[node("input", GraphNodeType.INPUT), node("transform"), node("output", GraphNodeType.OUTPUT), node("orphan")])
    assert validate_execution_graph(invalid).status is GraphValidationStatus.FAIL
    output_flow = graph(nodes=[node("input", GraphNodeType.INPUT), node("transform"), node("output", GraphNodeType.OUTPUT), node("later")], edges=[edge("input", "transform"), edge("transform", "output"), edge("output", "later")])
    assert validate_execution_graph(output_flow).status is GraphValidationStatus.FAIL


def test_dependency_semantic_attacks_fail_validation() -> None:
    wrong_tool_result = graph(edges=[edge("input", "transform", GraphDependencyType.TOOL_RESULT), edge("transform", "output")])
    unused_retrieval = graph(nodes=[node("input", GraphNodeType.INPUT), node("retrieval", GraphNodeType.RETRIEVAL, ComputationalCapability.RETRIEVAL), node("output", GraphNodeType.OUTPUT)], edges=[edge("input", "retrieval")])
    no_validation_input = graph(nodes=[node("input", GraphNodeType.INPUT), node("validation", GraphNodeType.VALIDATION), node("output", GraphNodeType.OUTPUT)], edges=[edge("input", "output")])
    assert all(validate_execution_graph(item).status is GraphValidationStatus.FAIL for item in (wrong_tool_result, unused_retrieval, no_validation_input))


def test_invalid_graph_cannot_transform_and_validation_fail_cannot_become_ready() -> None:
    invalid = graph(nodes=[node("input", GraphNodeType.INPUT), node("transform"), node("output", GraphNodeType.OUTPUT), node("orphan")])
    validation = validate_execution_graph(invalid)
    with pytest.raises(ValueError, match="validation"):
        transform_execution_graph(invalid)
    assert evaluate_graph_readiness(invalid, validation).status is GraphReadinessStatus.BLOCKED


def test_stale_passing_validation_cannot_make_a_mutated_cycle_ready() -> None:
    escaped = graph()
    passing = validate_execution_graph(escaped)
    object.__setattr__(escaped, "edges", (edge("input", "transform"), edge("transform", "output"), edge("output", "input")))
    assert evaluate_graph_readiness(escaped, passing).status is GraphReadinessStatus.BLOCKED


@pytest.mark.parametrize("field", ["model_id", "provider", "hardware", "placement", "scheduler_assignment", "runtime_process", "precision", "migration", "speculative_execution"])
def test_nested_or_graph_physical_leakage_cannot_become_ready(field: str) -> None:
    escaped = graph()
    object.__setattr__(escaped.nodes[1], field, "leak")
    assert evaluate_graph_readiness(escaped, validate_execution_graph(escaped)).status is GraphReadinessStatus.BLOCKED


def test_identical_failures_are_deterministic_and_do_not_mutate_artifacts() -> None:
    escaped = graph()
    validation = validate_execution_graph(escaped)
    object.__setattr__(escaped, "provenance", ())
    before = (escaped.nodes, escaped.edges, validation)
    first = evaluate_graph_readiness(escaped, validation)
    assert first == evaluate_graph_readiness(escaped, validation)
    assert (escaped.nodes, escaped.edges, validation) == before
