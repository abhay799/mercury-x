from dataclasses import FrozenInstanceError, fields
from datetime import UTC, datetime

import pytest

from mercury.contracts.workload_request import WorkloadRequest
from mercury.gateway.constraints import canonicalize_gateway_constraints
from mercury.gateway.identity import GatewayIdentity
from mercury.gateway.models import GatewayRequestEnvelope, GatewayValidationEvidence, GatewayValidationStatus
from mercury.gateway.normalization import normalize_gateway_request
from mercury.graph.builder import build_execution_graph
from mercury.graph.models import (
    ExecutionGraph, ExecutionGraphEdge, ExecutionGraphNode, GraphDependencyType, GraphNodeType,
)
from mercury.graph.validation import GraphValidationStatus, validate_execution_graph
from mercury.intelligence.models import ComputationalCapability, Evidence
from mercury.intelligence.pipeline import analyze_workload


def node(node_id: str, node_type: GraphNodeType = GraphNodeType.TRANSFORM, capability: ComputationalCapability = ComputationalCapability.GENERATION) -> ExecutionGraphNode:
    return ExecutionGraphNode(node_id, node_type, f"logical {node_type.value}", [capability], [Evidence("phase2", "explicit capability")])


def edge(source: str, target: str, dependency: GraphDependencyType = GraphDependencyType.DATA) -> ExecutionGraphEdge:
    return ExecutionGraphEdge(source, target, dependency, [Evidence("graph", "logical dependency")])


def graph(nodes=None, edges=None) -> ExecutionGraph:
    nodes = nodes or [node("input", GraphNodeType.INPUT), node("transform"), node("output", GraphNodeType.OUTPUT)]
    edges = edges if edges is not None else [edge("input", "transform"), edge("transform", "output")]
    return ExecutionGraph("graph-1", "request-1", "workload-1", "session-1", nodes, edges, [Evidence("phase2", "graph provenance")])


def issue_ids(result) -> set[str]:
    return {issue.issue_id for issue in result.issues}


def tool_pipeline_graph() -> ExecutionGraph:
    request = WorkloadRequest(
        workload_id="workload-1", session_id="session-1", task_type="inference",
        input={"text": "hello", "tool_use": True}, context={}, latency_target_ms=100.0,
        quality_target=0.9, privacy_level="confidential",
    )
    identity = GatewayIdentity(request_id="request-1", workload_id="workload-1", session_id="session-1")
    normalized = normalize_gateway_request(GatewayRequestEnvelope(
        gateway_request_id="gateway-request-1", identity=identity, workload_request=request,
        received_at=datetime(2026, 9, 16, tzinfo=UTC), normalized=False,
        validation_status=GatewayValidationStatus.ACCEPTED,
        validation_evidence=GatewayValidationEvidence(status=GatewayValidationStatus.ACCEPTED, reasons=()),
    ))
    assert normalized.normalized_request is not None
    return build_execution_graph(analyze_workload(normalized, canonicalize_gateway_constraints(identity, normalized.normalized_request)))


def test_valid_minimal_and_multi_stage_flow_passes_with_deterministic_topology() -> None:
    minimal = graph()
    multi = graph(
        [node("input", GraphNodeType.INPUT), node("pre", GraphNodeType.PREPROCESS), node("reason", GraphNodeType.REASONING, ComputationalCapability.REASONING), node("output", GraphNodeType.OUTPUT)],
        [edge("input", "pre"), edge("pre", "reason"), edge("reason", "output")],
    )
    result = validate_execution_graph(minimal)
    assert result.status is GraphValidationStatus.PASS
    assert result == validate_execution_graph(minimal)
    assert validate_execution_graph(multi).status is GraphValidationStatus.PASS
    assert result.topological_node_ids == ("input", "transform", "output")


def test_unreachable_orphan_disconnected_and_output_without_input_flow_fail() -> None:
    disconnected = graph(nodes=[node("input", GraphNodeType.INPUT), node("transform"), node("output", GraphNodeType.OUTPUT), node("orphan")])
    result = validate_execution_graph(disconnected)
    assert result.status is GraphValidationStatus.FAIL
    assert {"orphan_node", "processing_cannot_reach_output"}.intersection(issue_ids(result))
    no_output_flow = graph(nodes=[node("input", GraphNodeType.INPUT), node("transform"), node("output", GraphNodeType.OUTPUT)], edges=[edge("input", "transform")])
    assert validate_execution_graph(no_output_flow).status is GraphValidationStatus.FAIL


def test_invalid_input_output_and_transform_semantics_fail() -> None:
    invalid_input = graph(nodes=[node("input", GraphNodeType.INPUT), node("transform"), node("output", GraphNodeType.OUTPUT), node("prior")], edges=[edge("prior", "input"), edge("input", "transform"), edge("transform", "output")])
    invalid_output = graph(nodes=[node("input", GraphNodeType.INPUT), node("transform"), node("output", GraphNodeType.OUTPUT), node("after")], edges=[edge("input", "transform"), edge("transform", "output"), edge("output", "after")])
    no_transform_input = graph(nodes=[node("input", GraphNodeType.INPUT), node("transform"), node("output", GraphNodeType.OUTPUT)], edges=[edge("input", "output")])
    assert validate_execution_graph(invalid_input).status is GraphValidationStatus.FAIL
    assert validate_execution_graph(invalid_output).status is GraphValidationStatus.FAIL
    assert validate_execution_graph(no_transform_input).status is GraphValidationStatus.FAIL


def test_retrieval_tool_validation_and_aggregate_data_flow_rules() -> None:
    retrieval = graph(nodes=[node("input", GraphNodeType.INPUT), node("retrieval", GraphNodeType.RETRIEVAL, ComputationalCapability.RETRIEVAL), node("output", GraphNodeType.OUTPUT)], edges=[edge("input", "retrieval")])
    invalid_tool = graph(nodes=[node("input", GraphNodeType.INPUT), node("transform"), node("output", GraphNodeType.OUTPUT)], edges=[edge("input", "transform", GraphDependencyType.TOOL_RESULT), edge("transform", "output")])
    aggregate = graph(nodes=[node("input", GraphNodeType.INPUT), node("aggregate", GraphNodeType.AGGREGATE), node("output", GraphNodeType.OUTPUT)], edges=[edge("input", "aggregate"), edge("aggregate", "output")])
    assert validate_execution_graph(retrieval).status is GraphValidationStatus.FAIL
    assert validate_execution_graph(invalid_tool).status is GraphValidationStatus.FAIL
    assert validate_execution_graph(aggregate).status is GraphValidationStatus.FAIL


def test_valid_context_control_and_tool_result_dependencies_are_accepted() -> None:
    tool_graph = graph(
        [node("input", GraphNodeType.INPUT), node("tool", GraphNodeType.TOOL, ComputationalCapability.TOOL_USE), node("reason", GraphNodeType.REASONING, ComputationalCapability.REASONING), node("output", GraphNodeType.OUTPUT)],
        [edge("input", "tool", GraphDependencyType.CONTROL), edge("tool", "reason", GraphDependencyType.TOOL_RESULT), edge("reason", "output", GraphDependencyType.CONTEXT)],
    )
    assert validate_execution_graph(tool_graph).status is GraphValidationStatus.PASS


def test_task2_tool_graph_uses_valid_tool_result_flow() -> None:
    assert validate_execution_graph(tool_pipeline_graph()).status is GraphValidationStatus.PASS


def test_cycle_and_escaped_malformed_states_fail_closed_without_rewrite() -> None:
    malformed = graph()
    original_nodes, original_edges = malformed.nodes, malformed.edges
    object.__setattr__(malformed, "edges", (edge("input", "transform"), edge("transform", "output"), edge("output", "input")))
    result = validate_execution_graph(malformed)
    assert result.status is GraphValidationStatus.FAIL
    assert malformed.nodes == original_nodes
    assert malformed.edges != original_edges


def test_validation_result_and_issue_collections_are_immutable_and_logical_only() -> None:
    result = validate_execution_graph(graph())
    forbidden = {"model_id", "provider", "model_family", "cpu", "gpu", "hardware", "device", "region", "placement", "scheduler", "execution_graph_runtime", "runtime_process", "migration", "speculative_execution", "cost_optimization"}
    with pytest.raises(FrozenInstanceError):
        result.status = GraphValidationStatus.FAIL  # type: ignore[misc]
    with pytest.raises(AttributeError):
        result.issues.append(result.issues[0])  # type: ignore[attr-defined]
    assert forbidden.isdisjoint({field.name for field in fields(result)})
