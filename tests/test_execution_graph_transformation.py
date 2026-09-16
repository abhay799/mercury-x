from dataclasses import FrozenInstanceError, fields

import pytest

from mercury.graph.models import ExecutionGraph, ExecutionGraphEdge, ExecutionGraphNode, GraphDependencyType, GraphNodeType
from mercury.graph.transformation import GraphTransformationType, transform_execution_graph
from mercury.graph.validation import GraphValidationStatus, validate_execution_graph
from mercury.intelligence.models import (
    ComputationalCapability, ContextMagnitude, ContextRequirement, Evidence, LatencySensitivity,
    PrivacyRequirement, QualityRequirement, ReasoningComplexity, ToolRequirement, WorkloadIntelligenceProfile, WorkloadModality,
)


def profile(complexity=ReasoningComplexity.MINIMAL, capabilities=(ComputationalCapability.GENERATION,)) -> WorkloadIntelligenceProfile:
    return WorkloadIntelligenceProfile(
        "request-1", "workload-1", "session-1", [WorkloadModality.TEXT], complexity,
        ContextRequirement(ContextMagnitude.SHORT), ToolRequirement(False), LatencySensitivity.BATCH,
        QualityRequirement.STANDARD, PrivacyRequirement.CONFIDENTIAL, capabilities, 0.5,
        [Evidence("phase2", "explicit intelligence")],
    )


def node(node_id, node_type, capability=ComputationalCapability.GENERATION):
    return ExecutionGraphNode(node_id, node_type, f"logical {node_type.value}", [capability], [Evidence("phase2", "logical node evidence")])


def edge(source, target, kind=GraphDependencyType.DATA):
    return ExecutionGraphEdge(source, target, kind, [Evidence("graph", "logical dependency")])


def graph(nodes=None, edges=None, intelligence=None):
    nodes = nodes or [node("input", GraphNodeType.INPUT), node("transform", GraphNodeType.TRANSFORM), node("output", GraphNodeType.OUTPUT)]
    edges = edges if edges is not None else [edge("input", "transform"), edge("transform", "output")]
    return ExecutionGraph("graph-1", "request-1", "workload-1", "session-1", nodes, edges, [Evidence("phase2", "graph provenance")], intelligence_profile=intelligence)


def test_valid_graph_transforms_as_deterministic_no_op_with_identity_preserved() -> None:
    source = graph()
    first = transform_execution_graph(source)
    second = transform_execution_graph(source)
    assert first == second
    assert first.graph == source
    assert first.changed is False
    assert first.records[0].transformation_type is GraphTransformationType.NO_OP
    assert (first.graph.request_id, first.graph.workload_id, first.graph.session_id) == ("request-1", "workload-1", "session-1")


def test_invalid_graph_is_rejected_before_transformation() -> None:
    invalid = graph(nodes=[node("input", GraphNodeType.INPUT), node("transform", GraphNodeType.TRANSFORM), node("output", GraphNodeType.OUTPUT), node("orphan", GraphNodeType.TRANSFORM)])
    assert validate_execution_graph(invalid).status is GraphValidationStatus.FAIL
    with pytest.raises(ValueError, match="validation"):
        transform_execution_graph(invalid)


def test_high_and_deep_single_reasoning_stage_decompose_bounded_and_idempotently() -> None:
    for complexity in (ReasoningComplexity.HIGH, ReasoningComplexity.DEEP):
        intelligence = profile(complexity, (ComputationalCapability.REASONING,))
        source = graph([node("input", GraphNodeType.INPUT), node("reason", GraphNodeType.REASONING, ComputationalCapability.REASONING), node("output", GraphNodeType.OUTPUT)], [edge("input", "reason"), edge("reason", "output")], intelligence)
        result = transform_execution_graph(source)
        reasoning = [item.node_id for item in result.graph.nodes if item.node_type is GraphNodeType.REASONING]
        assert reasoning == ["reason-stage-1", "reason-stage-2"]
        assert transform_execution_graph(result.graph).graph == result.graph


def test_structured_output_path_and_existing_preprocessing_are_not_duplicated() -> None:
    intelligence = profile(capabilities=(ComputationalCapability.STRUCTURED_OUTPUT, ComputationalCapability.VISION))
    source = graph(
        [node("input", GraphNodeType.INPUT), node("pre", GraphNodeType.PREPROCESS, ComputationalCapability.VISION), node("transform", GraphNodeType.TRANSFORM), node("validation", GraphNodeType.VALIDATION, ComputationalCapability.STRUCTURED_OUTPUT), node("output", GraphNodeType.OUTPUT)],
        [edge("input", "pre"), edge("pre", "transform"), edge("transform", "validation"), edge("validation", "output")], intelligence,
    )
    result = transform_execution_graph(source)
    assert sum(item.node_type is GraphNodeType.PREPROCESS for item in result.graph.nodes) == 1
    assert sum(item.node_type is GraphNodeType.VALIDATION for item in result.graph.nodes) == 1


def test_aggregation_is_inserted_only_for_meaningful_multi_branch_flow() -> None:
    source = graph(
        [node("input", GraphNodeType.INPUT), node("retrieval", GraphNodeType.RETRIEVAL, ComputationalCapability.RETRIEVAL), node("tool", GraphNodeType.TOOL, ComputationalCapability.TOOL_USE), node("reason", GraphNodeType.REASONING, ComputationalCapability.REASONING), node("output", GraphNodeType.OUTPUT)],
        [edge("input", "retrieval"), edge("input", "tool", GraphDependencyType.CONTROL), edge("retrieval", "reason"), edge("tool", "reason", GraphDependencyType.TOOL_RESULT), edge("reason", "output")],
    )
    result = transform_execution_graph(source)
    assert GraphNodeType.AGGREGATE in {item.node_type for item in result.graph.nodes}
    assert any(record.transformation_type is GraphTransformationType.AGGREGATION_INSERTION for record in result.records)
    assert validate_execution_graph(result.graph).status is GraphValidationStatus.PASS


def test_source_is_not_mutated_and_result_records_are_immutable_and_logical_only() -> None:
    source = graph()
    before = source
    result = transform_execution_graph(source)
    forbidden = {"model_id", "provider", "model_family", "cpu", "gpu", "hardware", "device", "host", "region", "placement", "scheduler_assignment", "runtime_process", "container", "precision", "speculative_execution", "migration", "cost_optimization"}
    assert source == before
    with pytest.raises(FrozenInstanceError):
        result.changed = True  # type: ignore[misc]
    with pytest.raises(AttributeError):
        result.records.append(result.records[0])  # type: ignore[attr-defined]
    assert forbidden.isdisjoint({field.name for field in fields(result)})
