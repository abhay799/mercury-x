"""Controlled, deterministic transformations of validated logical graphs."""

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
from mercury.graph.validation import GraphValidationStatus, validate_execution_graph
from mercury.intelligence.models import Evidence, ReasoningComplexity


class GraphTransformationType(str, Enum):
    REASONING_DECOMPOSITION = "reasoning_decomposition"
    STRUCTURED_OUTPUT_NORMALIZATION = "structured_output_normalization"
    AGGREGATION_INSERTION = "aggregation_insertion"
    PREPROCESS_NORMALIZATION = "preprocess_normalization"
    REDUNDANT_STAGE_NORMALIZATION = "redundant_stage_normalization"
    NO_OP = "no_op"


@dataclass(frozen=True)
class GraphTransformationRecord:
    transformation_type: GraphTransformationType
    affected_node_ids: tuple[str, ...]
    generated_node_ids: tuple[str, ...]
    reason: str
    changed: bool

    def __post_init__(self) -> None:
        if not self.reason.strip():
            raise ValueError("reason must be nonblank")
        for field_name in ("affected_node_ids", "generated_node_ids"):
            values = tuple(sorted(set(getattr(self, field_name))))
            if any(not isinstance(value, str) or not value.strip() for value in values):
                raise ValueError(f"{field_name} must be nonblank")
            object.__setattr__(self, field_name, values)


@dataclass(frozen=True)
class ExecutionGraphTransformationResult:
    graph: ExecutionGraph
    records: tuple[GraphTransformationRecord, ...]
    changed: bool

    def __post_init__(self) -> None:
        records = tuple(sorted(set(self.records), key=lambda item: (item.transformation_type.value, item.affected_node_ids, item.generated_node_ids)))
        if not records:
            raise ValueError("records must not be empty")
        if self.changed != any(record.changed for record in records):
            raise ValueError("changed must match transformation records")
        object.__setattr__(self, "records", records)


def _record(kind: GraphTransformationType, affected: tuple[str, ...], generated: tuple[str, ...], reason: str, changed: bool) -> GraphTransformationRecord:
    return GraphTransformationRecord(kind, affected, generated, reason, changed)


def transform_execution_graph(graph: ExecutionGraph) -> ExecutionGraphTransformationResult:
    """Apply conservative logical transformations to an already valid graph."""
    before = validate_execution_graph(graph)
    if before.status is not GraphValidationStatus.PASS:
        raise ValueError("graph validation must PASS before transformation")

    nodes = list(graph.nodes)
    edges = list(graph.edges)
    records: list[GraphTransformationRecord] = []
    profile = graph.intelligence_profile

    if profile is not None and profile.reasoning_complexity in (ReasoningComplexity.HIGH, ReasoningComplexity.DEEP):
        reasoning = [node for node in nodes if node.node_type is GraphNodeType.REASONING]
        if len(reasoning) == 1:
            original = reasoning[0]
            first_id, second_id = f"{original.node_id}-stage-1", f"{original.node_id}-stage-2"
            first = ExecutionGraphNode(first_id, GraphNodeType.REASONING, original.purpose, original.required_capabilities, (*original.evidence, Evidence("graph.transformation", "bounded Phase 2 reasoning decomposition")), original.input_references, original.output_contract)
            second = ExecutionGraphNode(second_id, GraphNodeType.REASONING, original.purpose, original.required_capabilities, (*original.evidence, Evidence("graph.transformation", "bounded Phase 2 reasoning decomposition")), original.input_references, original.output_contract)
            incoming = [edge for edge in edges if edge.target_node_id == original.node_id]
            outgoing = [edge for edge in edges if edge.source_node_id == original.node_id]
            edges = [edge for edge in edges if edge not in incoming and edge not in outgoing]
            edges.extend(
                ExecutionGraphEdge(edge.source_node_id, first_id, edge.dependency_type, edge.evidence)
                for edge in incoming
            )
            edges.append(ExecutionGraphEdge(first_id, second_id, GraphDependencyType.DATA, (Evidence("graph.transformation", "decomposed reasoning stages exchange logical data"),)))
            edges.extend(
                ExecutionGraphEdge(second_id, edge.target_node_id, edge.dependency_type, edge.evidence)
                for edge in outgoing
            )
            nodes = [node for node in nodes if node.node_id != original.node_id] + [first, second]
            records.append(_record(GraphTransformationType.REASONING_DECOMPOSITION, (original.node_id,), (first_id, second_id), "HIGH or DEEP Phase 2 reasoning permits a bounded two-stage logical decomposition", True))

    nodes_by_id = {node.node_id: node for node in nodes}
    incoming_by_target: dict[str, list[ExecutionGraphEdge]] = {node_id: [] for node_id in nodes_by_id}
    for edge in edges:
        incoming_by_target[edge.target_node_id].append(edge)
    for target_id in sorted(incoming_by_target):
        incoming = incoming_by_target[target_id]
        if len(incoming) < 2 or nodes_by_id[target_id].node_type is GraphNodeType.AGGREGATE:
            continue
        if any(nodes_by_id[edge.source_node_id].node_type is GraphNodeType.AGGREGATE for edge in incoming):
            continue
        aggregate_id = f"node-aggregate-{target_id}"
        if aggregate_id in nodes_by_id:
            continue
        aggregate = ExecutionGraphNode(aggregate_id, GraphNodeType.AGGREGATE, "logical aggregation of multiple justified branches", (incoming[0] and nodes_by_id[incoming[0].source_node_id].required_capabilities[0],), (Evidence("graph.transformation", "multiple logical branches require explicit aggregation"),))
        edges = [edge for edge in edges if edge not in incoming]
        edges.extend(ExecutionGraphEdge(edge.source_node_id, aggregate_id, edge.dependency_type, edge.evidence) for edge in incoming)
        edges.append(ExecutionGraphEdge(aggregate_id, target_id, GraphDependencyType.DATA, (Evidence("graph.transformation", "aggregate produces logical data for downstream stage"),)))
        nodes.append(aggregate)
        nodes_by_id[aggregate_id] = aggregate
        records.append(_record(GraphTransformationType.AGGREGATION_INSERTION, tuple(edge.source_node_id for edge in incoming) + (target_id,), (aggregate_id,), "multiple incoming logical branches require an AGGREGATE stage", True))
        break

    if not records:
        records.append(_record(GraphTransformationType.NO_OP, (), (), "graph already satisfies conservative logical normalization rules", False))
        return ExecutionGraphTransformationResult(graph, tuple(records), False)

    transformed = ExecutionGraph(
        graph_id=graph.graph_id,
        request_id=graph.request_id,
        workload_id=graph.workload_id,
        session_id=graph.session_id,
        nodes=tuple(nodes),
        edges=tuple(edges),
        provenance=(*graph.provenance, Evidence("graph.transformation", "controlled logical transformation applied")),
        intelligence_profile=graph.intelligence_profile,
        status=graph.status,
        version=graph.version,
    )
    after = validate_execution_graph(transformed)
    if after.status is not GraphValidationStatus.PASS:
        raise ValueError("transformed graph validation must PASS")
    return ExecutionGraphTransformationResult(transformed, tuple(records), True)
