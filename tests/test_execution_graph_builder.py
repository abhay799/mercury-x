from dataclasses import FrozenInstanceError, fields
from datetime import UTC, datetime

import pytest

from mercury.contracts.workload_request import WorkloadRequest
from mercury.gateway.constraints import canonicalize_gateway_constraints
from mercury.gateway.identity import GatewayIdentity
from mercury.gateway.models import GatewayRequestEnvelope, GatewayValidationEvidence, GatewayValidationStatus
from mercury.gateway.normalization import normalize_gateway_request
from mercury.graph.builder import build_execution_graph
from mercury.graph.models import ExecutionGraph, GraphNodeType
from mercury.intelligence.pipeline import PipelineStatus, analyze_workload


def phase2(**overrides: object):
    values: dict[str, object] = {
        "workload_id": "workload-1", "session_id": "session-1", "task_type": "inference",
        "input": {"text": "hello"}, "context": {}, "latency_target_ms": 100.0,
        "quality_target": 0.9, "cost_budget": None, "privacy_level": "confidential",
        "priority": 50, "hardware_constraints": (),
    }
    values.update(overrides)
    request = WorkloadRequest(**values)
    identity = GatewayIdentity(request_id="request-1", workload_id="workload-1", session_id="session-1")
    envelope = GatewayRequestEnvelope(
        gateway_request_id="gateway-request-1", identity=identity, workload_request=request,
        received_at=datetime(2026, 9, 16, tzinfo=UTC), normalized=False,
        validation_status=GatewayValidationStatus.ACCEPTED,
        validation_evidence=GatewayValidationEvidence(status=GatewayValidationStatus.ACCEPTED, reasons=()),
    )
    normalization = normalize_gateway_request(envelope)
    assert normalization.normalized_request is not None
    return analyze_workload(normalization, canonicalize_gateway_constraints(identity, normalization.normalized_request)), request


def node_types(graph: ExecutionGraph) -> set[GraphNodeType]:
    return {node.node_type for node in graph.nodes}


def test_valid_text_workload_builds_deterministic_minimal_input_to_output_graph() -> None:
    result, _ = phase2()
    first = build_execution_graph(result)
    second = build_execution_graph(result)
    assert first == second
    assert (first.nodes[0].node_type, first.nodes[-1].node_type) == (GraphNodeType.INPUT, GraphNodeType.OUTPUT)


def test_reasoning_retrieval_and_tool_capabilities_add_justified_nodes() -> None:
    result, _ = phase2(input={"text": "hello", "tool_use": True}, context={"references": ["retrieval://1"]})
    types = node_types(build_execution_graph(result))
    assert {GraphNodeType.RETRIEVAL, GraphNodeType.TOOL, GraphNodeType.REASONING}.issubset(types)


def test_structured_output_and_visual_modality_add_validation_and_preprocessing() -> None:
    structured, _ = phase2(input={"text": "hello", "structured_output_required": True})
    visual, _ = phase2(input={"images": ["image-1"]})
    assert GraphNodeType.VALIDATION in node_types(build_execution_graph(structured))
    assert GraphNodeType.PREPROCESS in node_types(build_execution_graph(visual))


def test_multimodal_and_reasoning_complexity_decompose_deterministically() -> None:
    result, _ = phase2(input={"text": "hello", "images": ["image-1"], "tool_use": True}, context={"long_context": True, "references": ["retrieval://1"]})
    graph = build_execution_graph(result)
    assert GraphNodeType.PREPROCESS in node_types(graph)
    assert [node.node_id for node in graph.nodes if node.node_type is GraphNodeType.REASONING] == ["node-reasoning-1", "node-reasoning-2"]


def test_absent_optional_capabilities_do_not_create_specialized_nodes() -> None:
    result, _ = phase2()
    types = node_types(build_execution_graph(result))
    assert GraphNodeType.RETRIEVAL not in types
    assert GraphNodeType.TOOL not in types
    assert GraphNodeType.VALIDATION not in types


def test_phase2_identity_provenance_dag_and_node_evidence_are_preserved() -> None:
    result, _ = phase2()
    graph = build_execution_graph(result)
    assert (graph.request_id, graph.workload_id, graph.session_id) == (result.request_id, result.workload_id, result.session_id)
    assert graph.intelligence_profile is result.profile
    assert all(node.evidence and node.evidence[0].reason.strip() for node in graph.nodes)
    assert all(edge.source_node_id in {node.node_id for node in graph.nodes} and edge.target_node_id in {node.node_id for node in graph.nodes} for edge in graph.edges)


def test_phase2_input_is_not_mutated_and_graph_is_immutable() -> None:
    result, request = phase2()
    before = (result, request.model_dump(mode="python"))
    graph = build_execution_graph(result)
    assert (result, request.model_dump(mode="python")) == before
    with pytest.raises(FrozenInstanceError):
        graph.graph_id = "changed"  # type: ignore[misc]


def test_pipeline_fail_identity_mismatch_and_unsupported_state_fail_closed() -> None:
    result, _ = phase2()
    object.__setattr__(result, "status", PipelineStatus.FAIL)
    with pytest.raises(ValueError, match="pipeline"):
        build_execution_graph(result)
    mismatch, _ = phase2()
    object.__setattr__(mismatch, "request_id", "other")
    with pytest.raises(ValueError, match="identity"):
        build_execution_graph(mismatch)
    unsupported, _ = phase2()
    object.__setattr__(unsupported.profile, "required_capabilities", ("unknown",))
    with pytest.raises(ValueError, match="capability"):
        build_execution_graph(unsupported)


def test_logical_graph_exposes_no_resource_selection_fields() -> None:
    forbidden = {"model_id", "provider", "model_family", "cpu", "gpu", "accelerator", "hardware", "device", "host", "region", "placement", "scheduler_assignment", "runtime_process", "container", "migration", "speculative_execution", "cost_optimization", "precision_selection"}
    assert forbidden.isdisjoint({field.name for field in fields(ExecutionGraph)})
