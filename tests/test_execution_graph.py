from uuid import uuid4

from mercury.graph.models import (
    AIExecutionGraph,
    EdgeType,
    ExecutionEdge,
    ExecutionNode,
    NodeType,
)


def test_create_execution_graph():
    workload_id = uuid4()

    input_node = ExecutionNode(
        name="Input",
        node_type=NodeType.INPUT,
        capability_required="input_processing",
    )

    reasoning_node = ExecutionNode(
        name="Deep Reasoning",
        node_type=NodeType.REASONING,
        capability_required="deep_reasoning",
        max_latency_ms=5000,
    )

    output_node = ExecutionNode(
        name="Output",
        node_type=NodeType.OUTPUT,
        capability_required="output_generation",
    )

    edge_1 = ExecutionEdge(
        source_node=input_node.node_id,
        target_node=reasoning_node.node_id,
        edge_type=EdgeType.DATA,
    )

    edge_2 = ExecutionEdge(
        source_node=reasoning_node.node_id,
        target_node=output_node.node_id,
        edge_type=EdgeType.DATA,
    )

    graph = AIExecutionGraph(
        workload_id=workload_id,
        nodes=[
            input_node,
            reasoning_node,
            output_node,
        ],
        edges=[
            edge_1,
            edge_2,
        ],
        entry_nodes=[input_node.node_id],
        terminal_nodes=[output_node.node_id],
    )

    assert len(graph.nodes) == 3
    assert len(graph.edges) == 2
    assert graph.entry_nodes == [input_node.node_id]
    assert graph.terminal_nodes == [output_node.node_id]


def test_legacy_ai_execution_graph_remains_unchanged():
    graph = AIExecutionGraph(workload_id=uuid4())

    assert graph.graph_version == "0.1"
    assert graph.nodes == []
