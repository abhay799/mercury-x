from dataclasses import FrozenInstanceError, fields

import pytest

from mercury.graph.models import (
    ExecutionGraph,
    ExecutionGraphEdge,
    ExecutionGraphNode,
    GraphDependencyType,
    GraphNodeType,
)
from mercury.intelligence.models import ComputationalCapability, Evidence


def node(node_id: str, node_type: GraphNodeType = GraphNodeType.INPUT) -> ExecutionGraphNode:
    return ExecutionGraphNode(
        node_id=node_id,
        node_type=node_type,
        purpose=f"logical {node_type.value} purpose",
        required_capabilities=[ComputationalCapability.GENERATION],
        evidence=[Evidence("phase2.profile", "explicit workload capability")],
    )


def graph(**changes: object) -> ExecutionGraph:
    values: dict[str, object] = {
        "graph_id": "graph-1", "request_id": "request-1", "workload_id": "workload-1", "session_id": "session-1",
        "nodes": [node("input")], "edges": [],
        "provenance": [Evidence("phase2.profile", "logical graph contract baseline")],
    }
    values.update(changes)
    return ExecutionGraph(**values)  # type: ignore[arg-type]


def test_valid_minimal_graph_is_immutable_and_deterministic() -> None:
    first = graph()
    second = graph()
    assert first == second
    assert isinstance(first.nodes, tuple)
    with pytest.raises(FrozenInstanceError):
        first.graph_id = "changed"  # type: ignore[misc]


def test_valid_multi_node_graph_preserves_sorted_nodes_edges_and_capabilities() -> None:
    output = node("output", GraphNodeType.OUTPUT)
    edge = ExecutionGraphEdge("input", "output", GraphDependencyType.DATA, [Evidence("graph", "data dependency")])
    result = graph(nodes=[output, node("input")], edges=[edge])
    assert tuple(item.node_id for item in result.nodes) == ("input", "output")
    assert result.nodes[0].required_capabilities == (ComputationalCapability.GENERATION,)
    assert result.edges[0].source_node_id == "input"


def test_node_and_edge_contracts_validate_nonblank_fields() -> None:
    assert node("input").node_type is GraphNodeType.INPUT
    assert ExecutionGraphEdge("a", "b", GraphDependencyType.CONTROL, [Evidence("graph", "control")]).dependency_type is GraphDependencyType.CONTROL
    with pytest.raises(ValueError, match="node_id"):
        node(" ")
    with pytest.raises(ValueError, match="purpose"):
        ExecutionGraphNode(
            "x", GraphNodeType.INPUT, " ", [ComputationalCapability.GENERATION],
            evidence=[Evidence("x", "reason")],
        )


def test_duplicate_dangling_and_self_edges_are_rejected() -> None:
    with pytest.raises(ValueError, match="unique"):
        graph(nodes=[node("input"), node("input")])
    with pytest.raises(ValueError, match="source"):
        graph(edges=[ExecutionGraphEdge("missing", "input", GraphDependencyType.DATA, [Evidence("graph", "bad")])])
    with pytest.raises(ValueError, match="target"):
        graph(edges=[ExecutionGraphEdge("input", "missing", GraphDependencyType.DATA, [Evidence("graph", "bad")])])
    with pytest.raises(ValueError, match="self"):
        graph(edges=[ExecutionGraphEdge("input", "input", GraphDependencyType.DATA, [Evidence("graph", "bad")])])


def test_cycle_is_rejected_for_dag_baseline() -> None:
    first, second = node("first"), node("second")
    edges = [
        ExecutionGraphEdge("first", "second", GraphDependencyType.DATA, [Evidence("graph", "forward")]),
        ExecutionGraphEdge("second", "first", GraphDependencyType.DATA, [Evidence("graph", "backward")]),
    ]
    with pytest.raises(ValueError, match="cycle"):
        graph(nodes=[first, second], edges=edges)


@pytest.mark.parametrize("field", ["graph_id", "request_id", "workload_id", "session_id"])
def test_blank_graph_identity_is_rejected(field: str) -> None:
    with pytest.raises(ValueError, match=field):
        graph(**{field: " "})


def test_collections_and_boundary_fields_are_immutable_and_logical_only() -> None:
    result = graph()
    forbidden = {"model_id", "provider", "model_family", "cpu", "gpu", "hardware", "device", "physical_host", "region", "placement", "scheduler_assignment", "runtime_process", "migration", "speculative_execution"}
    with pytest.raises(AttributeError):
        result.nodes.append(node("other"))  # type: ignore[attr-defined]
    assert forbidden.isdisjoint({field.name for field in fields(ExecutionGraph)})
