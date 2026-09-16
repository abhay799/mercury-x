"""Read-only semantic validation for logical execution-graph data flow."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from mercury.graph.models import (
    ExecutionGraph,
    ExecutionGraphEdge,
    ExecutionGraphNode,
    GraphDependencyType,
    GraphNodeType,
)
from mercury.intelligence.models import ComputationalCapability, Evidence, WorkloadIntelligenceProfile


class GraphValidationStatus(str, Enum):
    PASS = "pass"
    DEGRADED = "degraded"
    FAIL = "fail"


class GraphValidationSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class GraphValidationIssue:
    issue_id: str
    severity: GraphValidationSeverity
    reason: str
    node_id: str | None = None
    edge: tuple[str, str] | None = None

    def __post_init__(self) -> None:
        if not self.issue_id.strip():
            raise ValueError("issue_id must be nonblank")
        if not self.reason.strip():
            raise ValueError("reason must be nonblank")


@dataclass(frozen=True)
class ExecutionGraphValidationResult:
    graph_id: str
    status: GraphValidationStatus
    issues: tuple[GraphValidationIssue, ...]
    topological_node_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        issues = tuple(sorted(set(self.issues), key=lambda item: (item.issue_id, item.node_id or "", item.edge or ())))
        if any(not isinstance(item, GraphValidationIssue) for item in issues):
            raise ValueError("issues must contain GraphValidationIssue values")
        if self.status is GraphValidationStatus.PASS and issues:
            raise ValueError("passing validation cannot contain issues")
        object.__setattr__(self, "issues", issues)
        object.__setattr__(self, "topological_node_ids", tuple(self.topological_node_ids))


def validate_execution_graph(graph: ExecutionGraph) -> ExecutionGraphValidationResult:
    """Analyze a logical graph without changing its nodes, edges, or provenance."""
    if not isinstance(graph, ExecutionGraph):
        raise ValueError("graph must be an ExecutionGraph")
    issues: list[GraphValidationIssue] = []

    def error(issue_id: str, reason: str, node_id: str | None = None, edge: tuple[str, str] | None = None) -> None:
        issues.append(GraphValidationIssue(issue_id, GraphValidationSeverity.ERROR, reason, node_id, edge))

    if any(not isinstance(value, str) or not value.strip() for value in (graph.graph_id, graph.request_id, graph.workload_id, graph.session_id)):
        error("malformed_graph_identity", "graph identity fields must be nonblank")

    raw_nodes = tuple(graph.nodes)
    nodes: dict[str, ExecutionGraphNode] = {}
    for item in raw_nodes:
        if not isinstance(item, ExecutionGraphNode):
            error("unsupported_node_state", "graph contains an unsupported node state")
            continue
        if not isinstance(item.node_id, str) or not item.node_id.strip():
            error("malformed_node_identity", "node identity must be nonblank")
            continue
        if item.node_id in nodes:
            error("duplicate_node_identity", "node identities must be unique", item.node_id)
            continue
        if not isinstance(item.node_type, GraphNodeType):
            error("unsupported_node_type", "node type is unsupported", item.node_id)
            continue
        if not item.evidence or any(not isinstance(evidence, Evidence) or not evidence.source.strip() or not evidence.reason.strip() for evidence in item.evidence):
            error("malformed_node_evidence", "node evidence must be nonblank", item.node_id)
        nodes[item.node_id] = item

    valid_edges: list[ExecutionGraphEdge] = []
    for item in tuple(graph.edges):
        if not isinstance(item, ExecutionGraphEdge):
            error("unsupported_dependency_state", "graph contains an unsupported dependency state")
            continue
        edge_key = (item.source_node_id, item.target_node_id)
        if not isinstance(item.dependency_type, GraphDependencyType):
            error("unsupported_dependency_type", "dependency type is unsupported", edge=edge_key)
            continue
        if item.source_node_id not in nodes:
            error("dangling_edge_source", "edge source node does not exist", edge=edge_key)
            continue
        if item.target_node_id not in nodes:
            error("dangling_edge_target", "edge target node does not exist", edge=edge_key)
            continue
        if item.source_node_id == item.target_node_id:
            error("self_edge", "self-edge is not valid logical flow", edge=edge_key)
            continue
        if not item.evidence or any(not isinstance(evidence, Evidence) or not evidence.source.strip() or not evidence.reason.strip() for evidence in item.evidence):
            error("malformed_edge_evidence", "edge evidence must be nonblank", edge=edge_key)
        valid_edges.append(item)

    incoming = {node_id: [] for node_id in nodes}
    outgoing = {node_id: [] for node_id in nodes}
    for item in valid_edges:
        incoming[item.target_node_id].append(item)
        outgoing[item.source_node_id].append(item)

    order, has_cycle = _topological_order(nodes, outgoing, incoming)
    if has_cycle:
        error("cycle", "logical graph contains a dependency cycle")
    inputs = tuple(sorted(node_id for node_id, item in nodes.items() if item.node_type is GraphNodeType.INPUT))
    outputs = tuple(sorted(node_id for node_id, item in nodes.items() if item.node_type is GraphNodeType.OUTPUT))
    if not inputs:
        error("missing_input", "graph requires at least one INPUT node")
    if not outputs:
        error("missing_output", "graph requires at least one OUTPUT node")

    for node_id in inputs:
        if incoming[node_id]:
            error("input_has_dependency", "INPUT node must not depend on downstream flow", node_id)
    for node_id in outputs:
        if outgoing[node_id]:
            error("output_has_downstream_flow", "OUTPUT node must not feed processing nodes", node_id)
        if not any(item.dependency_type in (GraphDependencyType.DATA, GraphDependencyType.CONTEXT, GraphDependencyType.TOOL_RESULT) for item in incoming[node_id]):
            error("output_without_final_result", "OUTPUT node must consume a valid final result", node_id)

    reachable_from_input = _reachable(inputs, outgoing, forward=True)
    reaches_output = _reachable(outputs, incoming, forward=False)
    processing_types = set(GraphNodeType) - {GraphNodeType.INPUT, GraphNodeType.OUTPUT}
    for node_id, item in nodes.items():
        if item.node_type in processing_types:
            if node_id not in reachable_from_input:
                error("orphan_node", "processing node is unreachable from INPUT", node_id)
            if node_id not in reaches_output:
                error("processing_cannot_reach_output", "processing node cannot contribute to OUTPUT", node_id)
        if item.node_type in (GraphNodeType.PREPROCESS, GraphNodeType.TRANSFORM, GraphNodeType.VALIDATION) and not _has_data_like_input(incoming[node_id]):
            error("node_without_upstream_data", f"{item.node_type.value} node requires upstream logical data", node_id)
        if item.node_type is GraphNodeType.AGGREGATE and sum(edge.dependency_type in (GraphDependencyType.DATA, GraphDependencyType.CONTEXT, GraphDependencyType.TOOL_RESULT) for edge in incoming[node_id]) < 2:
            error("aggregate_missing_inputs", "AGGREGATE node requires multiple justified inputs", node_id)
        if item.node_type in (GraphNodeType.RETRIEVAL, GraphNodeType.TOOL) and not outgoing[node_id]:
            error("unused_specialized_node", f"{item.node_type.value} result has no downstream consumer", node_id)

    for item in valid_edges:
        source_type = nodes[item.source_node_id].node_type
        if item.dependency_type is GraphDependencyType.TOOL_RESULT and source_type is not GraphNodeType.TOOL:
            error("invalid_tool_result_producer", "TOOL_RESULT must originate from a TOOL node", edge=(item.source_node_id, item.target_node_id))
        if source_type is GraphNodeType.TOOL and item.dependency_type is not GraphDependencyType.TOOL_RESULT:
            error("tool_result_as_generic_dependency", "TOOL output must use TOOL_RESULT dependency semantics", edge=(item.source_node_id, item.target_node_id))

    _validate_capability_coverage(graph.intelligence_profile, nodes, error)
    result_status = GraphValidationStatus.FAIL if issues else GraphValidationStatus.PASS
    return ExecutionGraphValidationResult(graph.graph_id, result_status, tuple(issues), order)


def _has_data_like_input(edges: list[ExecutionGraphEdge]) -> bool:
    return any(edge.dependency_type in (GraphDependencyType.DATA, GraphDependencyType.CONTEXT, GraphDependencyType.TOOL_RESULT) for edge in edges)


def _reachable(start_nodes: tuple[str, ...], adjacency: dict[str, list[ExecutionGraphEdge]], *, forward: bool) -> set[str]:
    seen = set(start_nodes)
    ready = list(start_nodes)
    while ready:
        current = ready.pop(0)
        for edge in sorted(adjacency[current], key=lambda item: (item.source_node_id, item.target_node_id)):
            neighbor = edge.target_node_id if forward else edge.source_node_id
            if neighbor not in seen:
                seen.add(neighbor)
                ready.append(neighbor)
    return seen


def _topological_order(nodes: dict[str, ExecutionGraphNode], outgoing: dict[str, list[ExecutionGraphEdge]], incoming: dict[str, list[ExecutionGraphEdge]]) -> tuple[tuple[str, ...], bool]:
    counts = {node_id: len(edges) for node_id, edges in incoming.items()}
    ready = sorted(node_id for node_id, count in counts.items() if count == 0)
    order: list[str] = []
    while ready:
        current = ready.pop(0)
        order.append(current)
        for edge in sorted(outgoing[current], key=lambda item: item.target_node_id):
            counts[edge.target_node_id] -= 1
            if counts[edge.target_node_id] == 0:
                ready.append(edge.target_node_id)
        ready.sort()
    return tuple(order), len(order) != len(nodes)


def _validate_capability_coverage(profile: WorkloadIntelligenceProfile | None, nodes: dict[str, ExecutionGraphNode], error) -> None:
    if profile is None:
        return
    if not isinstance(profile, WorkloadIntelligenceProfile):
        error("unsupported_intelligence_profile", "graph intelligence profile is unsupported")
        return
    types = {node.node_type for node in nodes.values()}
    capabilities = profile.required_capabilities
    if ComputationalCapability.RETRIEVAL in capabilities and GraphNodeType.RETRIEVAL not in types:
        error("missing_retrieval_coverage", "RETRIEVAL capability lacks a logical RETRIEVAL node")
    if (ComputationalCapability.TOOL_USE in capabilities or ComputationalCapability.CODE_EXECUTION in capabilities) and GraphNodeType.TOOL not in types:
        error("missing_tool_coverage", "tool capability lacks a logical TOOL node")
    if ComputationalCapability.STRUCTURED_OUTPUT in capabilities and GraphNodeType.VALIDATION not in types:
        error("missing_structured_output_coverage", "STRUCTURED_OUTPUT capability lacks a logical VALIDATION node")
    if ComputationalCapability.VISION in capabilities and GraphNodeType.PREPROCESS not in types:
        error("missing_vision_coverage", "VISION capability lacks logical visual preprocessing")
