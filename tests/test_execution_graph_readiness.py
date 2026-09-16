from dataclasses import FrozenInstanceError, fields

import pytest

from mercury.graph.models import ExecutionGraph, ExecutionGraphEdge, ExecutionGraphNode, GraphDependencyType, GraphNodeType
from mercury.graph.readiness import GraphReadinessStatus, evaluate_graph_readiness
from mercury.graph.transformation import transform_execution_graph
from mercury.graph.validation import GraphValidationStatus, validate_execution_graph
from mercury.intelligence.models import ComputationalCapability, Evidence


def node(node_id, node_type=GraphNodeType.TRANSFORM):
    return ExecutionGraphNode(node_id, node_type, f"logical {node_type.value}", [ComputationalCapability.GENERATION], [Evidence("phase2", "logical evidence")])


def edge(source, target):
    return ExecutionGraphEdge(source, target, GraphDependencyType.DATA, [Evidence("graph", "logical flow")])


def graph(nodes=None, edges=None):
    nodes = nodes or [node("input", GraphNodeType.INPUT), node("transform"), node("output", GraphNodeType.OUTPUT)]
    edges = edges if edges is not None else [edge("input", "transform"), edge("transform", "output")]
    return ExecutionGraph("graph-1", "request-1", "workload-1", "session-1", nodes, edges, [Evidence("phase2", "graph provenance")])


def test_valid_minimal_and_transformed_graphs_are_ready_deterministically() -> None:
    source = graph()
    validation = validate_execution_graph(source)
    first = evaluate_graph_readiness(source, validation)
    assert first.status is GraphReadinessStatus.READY
    assert first == evaluate_graph_readiness(source, validation)
    transformed = transform_execution_graph(source)
    assert evaluate_graph_readiness(transformed.graph, validate_execution_graph(transformed.graph), transformed).status is GraphReadinessStatus.READY


def test_failed_validation_and_identity_mismatch_block_readiness() -> None:
    invalid = graph(nodes=[node("input", GraphNodeType.INPUT), node("transform"), node("output", GraphNodeType.OUTPUT), node("orphan")])
    failed = validate_execution_graph(invalid)
    assert failed.status is GraphValidationStatus.FAIL
    assert evaluate_graph_readiness(invalid, failed).status is GraphReadinessStatus.BLOCKED
    valid = graph()
    mismatch = validate_execution_graph(valid)
    object.__setattr__(mismatch, "graph_id", "other")
    assert evaluate_graph_readiness(valid, mismatch).status is GraphReadinessStatus.BLOCKED


def test_missing_graph_or_transformation_provenance_blocks_changed_graph() -> None:
    source = graph()
    object.__setattr__(source, "provenance", ())
    assert evaluate_graph_readiness(source, validate_execution_graph(source)).status is GraphReadinessStatus.BLOCKED
    source = graph()
    transformed = transform_execution_graph(source)
    object.__setattr__(transformed, "records", ())
    assert evaluate_graph_readiness(transformed.graph, validate_execution_graph(transformed.graph), transformed).status is GraphReadinessStatus.BLOCKED


@pytest.mark.parametrize("field", ["model_id", "provider", "hardware", "region", "placement", "scheduler_assignment", "runtime_process", "precision", "migration", "speculative_execution"])
def test_physical_execution_leakage_blocks_readiness(field: str) -> None:
    source = graph()
    object.__setattr__(source, field, "leak")
    assert evaluate_graph_readiness(source, validate_execution_graph(source)).status is GraphReadinessStatus.BLOCKED


def test_readiness_evidence_issues_and_source_artifacts_are_immutable() -> None:
    source = graph()
    validation = validate_execution_graph(source)
    before = (source, validation)
    result = evaluate_graph_readiness(source, validation)
    assert (source, validation) == before
    assert all(item.reason.strip() for item in result.evidence)
    with pytest.raises(FrozenInstanceError):
        result.status = GraphReadinessStatus.BLOCKED  # type: ignore[misc]
    with pytest.raises(AttributeError):
        result.issues.append(result.issues[0])  # type: ignore[attr-defined]


def test_readiness_result_exposes_no_physical_decision_fields() -> None:
    forbidden = {"model_id", "provider", "model_family", "cpu", "gpu", "hardware", "device", "host", "region", "placement", "scheduler", "runtime", "container", "precision", "migration", "speculative_execution", "cost_optimization"}
    assert forbidden.isdisjoint({field.name for field in fields(evaluate_graph_readiness(graph(), validate_execution_graph(graph())))})
