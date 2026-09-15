from datetime import datetime, timezone
import importlib
import pytest
from pydantic import ValidationError


def load(module: str, name: str):
    try:
        mod = importlib.import_module(module)
        return getattr(mod, name)
    except (ImportError, AttributeError) as exc:
        pytest.fail(f"Missing contract {module}.{name}: {exc}")


def test_workload_request_has_version_and_rejects_invalid_quality():
    WorkloadRequest = load("mercury.contracts.workload_request", "WorkloadRequest")
    item = WorkloadRequest(
        workload_id="wl-1",
        task_type="multimodal_analysis",
        input={"text": "inspect"},
        latency_target_ms=2000,
        quality_target=0.93,
        privacy_level="organization-only",
    )
    assert item.schema_version == "mercury.workload.request/v1"
    with pytest.raises(ValidationError):
        WorkloadRequest(
            workload_id="wl-2",
            task_type="analysis",
            input={},
            latency_target_ms=1000,
            quality_target=1.5,
            privacy_level="private",
        )


def test_workload_profile_captures_intelligence_requirements():
    WorkloadProfile = load("mercury.contracts.workload_profile", "WorkloadProfile")
    profile = WorkloadProfile(
        workload_id="wl-1",
        required_modalities=["text", "image"],
        reasoning_complexity="high",
        required_capabilities=["vision", "reasoning"],
        context_bytes=4096,
        latency_sensitive=True,
        quality_target=0.93,
        privacy_level="organization-only",
    )
    assert profile.schema_version == "mercury.workload.profile/v1"
    assert "vision" in profile.required_capabilities


def test_model_profile_declares_capabilities_without_placement_logic():
    ModelProfile = load("mercury.contracts.model_profile", "ModelProfile")
    model = ModelProfile(
        model_id="model-vision-1",
        provider="local",
        family="vision-language",
        version="1.0",
        capabilities=["vision", "generation"],
        supported_precisions=["fp16", "int8"],
        context_window_tokens=8192,
        min_memory_gb=4.0,
        capability_labels=["EXPERIMENTAL"],
    )
    assert model.schema_version == "mercury.model.profile/v1"
    assert model.min_memory_gb == 4.0


def test_hardware_profile_supports_simulated_or_measured_identity():
    HardwareProfile = load("mercury.contracts.hardware_profile", "HardwareProfile")
    hw = HardwareProfile(
        hardware_id="cpu-local-1",
        provider="local",
        hardware_type="CPU",
        memory_gb=16,
        available_memory_gb=8,
        supported_precisions=["fp32", "int8"],
        topology_tags=["local"],
        capability_labels=["PRODUCTION"],
        evidence_type="MEASURED",
    )
    assert hw.schema_version == "mercury.hardware.profile/v1"
    with pytest.raises(ValidationError):
        HardwareProfile(
            hardware_id="bad",
            provider="sim",
            hardware_type="GPU",
            memory_gb=4,
            available_memory_gb=8,
            evidence_type="SIMULATED",
        )


def test_execution_plan_is_physical_and_records_predicted_metrics():
    ExecutionPlan = load("mercury.contracts.execution_plan", "ExecutionPlan")
    plan = ExecutionPlan(
        plan_id="plan-1",
        workload_id="wl-1",
        graph_id="graph-1",
        model_assignments={"node-1": "model-1"},
        precision_assignments={"node-1": "int8"},
        hardware_assignments={"node-1": "cpu-local-1"},
        context_placements={"ctx-1": "RAM"},
        predicted_metrics={"latency_ms": 1400.0, "quality": 0.95},
        policy_version="policy-v1",
    )
    assert plan.schema_version == "mercury.execution.plan/v1"
    assert plan.hardware_assignments["node-1"] == "cpu-local-1"


def test_schedule_decision_records_selection_and_rejected_alternatives():
    ScheduleDecision = load("mercury.contracts.schedule_decision", "ScheduleDecision")
    CandidateAlternative = load("mercury.contracts.schedule_decision", "CandidateAlternative")
    decision = ScheduleDecision(
        decision_id="decision-1",
        execution_plan_id="plan-1",
        selected=True,
        reasons=["all hard constraints satisfied"],
        alternatives=[CandidateAlternative(plan_id="plan-2", rejection_reasons=["cost budget exceeded"])],
    )
    assert decision.schema_version == "mercury.schedule.decision/v1"
    assert decision.alternatives[0].rejection_reasons == ["cost budget exceeded"]


def test_runtime_event_is_timestamped_and_versioned():
    RuntimeEvent = load("mercury.contracts.runtime_event", "RuntimeEvent")
    event = RuntimeEvent(
        event_id="evt-1",
        execution_id="exec-1",
        node_id="node-1",
        event_type="node_started",
        status="RUNNING",
        timestamp=datetime.now(timezone.utc),
    )
    assert event.schema_version == "mercury.runtime.event/v1"


def test_telemetry_record_preserves_execution_evidence():
    TelemetryRecord = load("mercury.contracts.telemetry", "TelemetryRecord")
    now = datetime.now(timezone.utc)
    record = TelemetryRecord(
        request_id="req-1",
        workload_id="wl-1",
        execution_id="exec-1",
        node_id="node-1",
        model_id="model-1",
        hardware_id="cpu-local-1",
        scheduler_decision_id="decision-1",
        start_time=now,
        end_time=now,
        latency_ms=25.4,
        status="COMPLETED",
        resource_usage={"cpu_percent": 24.0},
    )
    assert record.schema_version == "mercury.telemetry.record/v1"
    assert record.latency_ms == 25.4


def test_slo_definition_and_result_separate_targets_from_evidence():
    SLODefinition = load("mercury.contracts.slo", "SLODefinition")
    SLOResult = load("mercury.contracts.slo", "SLOResult")
    slo = SLODefinition(
        slo_id="slo-1",
        version="1",
        max_p95_latency_ms=2000,
        min_quality=0.93,
        min_reliability=0.95,
        max_cost_per_request=0.10,
        privacy_rule="organization-only",
    )
    result = SLOResult(
        slo_result_id="slo-result-1",
        slo_definition_id="slo-1",
        workload_id="wl-1",
        execution_id="exec-1",
        satisfied=True,
        measurements={"p95_latency_ms": 1500, "quality": 0.95},
    )
    assert slo.schema_version == "mercury.slo.definition/v1"
    assert result.schema_version == "mercury.slo.result/v1"


def test_policy_set_preserves_hard_constraints_and_objectives():
    PolicySet = load("mercury.contracts.policy", "PolicySet")
    OptimizationObjective = load("mercury.contracts.policy", "OptimizationObjective")
    policy = PolicySet(
        policy_id="policy-1",
        version="1",
        hard_constraints={"privacy": "organization-only", "max_cost": 0.10},
        optimization_objectives=[OptimizationObjective(name="latency", direction="minimize", weight=0.6)],
    )
    assert policy.schema_version == "mercury.policy.set/v1"
    assert policy.hard_constraints["privacy"] == "organization-only"


def test_execution_graph_contract_is_versioned_and_logical():
    ExecutionGraph = load("mercury.contracts.execution_graph", "ExecutionGraph")
    GraphNode = load("mercury.contracts.execution_graph", "GraphNode")
    GraphEdge = load("mercury.contracts.execution_graph", "GraphEdge")

    graph = ExecutionGraph(
        graph_id="graph-1",
        workload_id="wl-1",
        graph_version="1",
        nodes=[
            GraphNode(node_id="input", name="Input", node_type="input", capability_required="input_processing"),
            GraphNode(node_id="reason", name="Reason", node_type="reasoning", capability_required="reasoning"),
            GraphNode(node_id="output", name="Output", node_type="output", capability_required="output_generation"),
        ],
        edges=[
            GraphEdge(edge_id="edge-1", source_node="input", target_node="reason", edge_type="data"),
            GraphEdge(edge_id="edge-2", source_node="reason", target_node="output", edge_type="data"),
        ],
        entry_nodes=["input"],
        terminal_nodes=["output"],
    )

    assert graph.schema_version == "mercury.execution.graph/v1"
    assert graph.graph_id == "graph-1"
    assert [node.node_id for node in graph.nodes] == ["input", "reason", "output"]


@pytest.mark.parametrize(
    "physical_field",
    ["model_assignments", "precision_assignments", "hardware_assignments", "context_placements"],
)
def test_execution_graph_contract_rejects_physical_execution_fields(physical_field):
    ExecutionGraph = load("mercury.contracts.execution_graph", "ExecutionGraph")
    GraphNode = load("mercury.contracts.execution_graph", "GraphNode")

    payload = {
        "graph_id": "graph-physical-fields",
        "workload_id": "wl-1",
        "nodes": [GraphNode(node_id="input", name="Input", node_type="input", capability_required="input_processing")],
        "entry_nodes": ["input"],
        "terminal_nodes": ["input"],
        physical_field: {"input": "not-logical"},
    }

    with pytest.raises(ValidationError):
        ExecutionGraph(**payload)


def test_execution_graph_contract_rejects_physical_assignments_hidden_in_metadata():
    ExecutionGraph = load("mercury.contracts.execution_graph", "ExecutionGraph")
    GraphNode = load("mercury.contracts.execution_graph", "GraphNode")

    node = GraphNode(node_id="input", name="Input", node_type="input", capability_required="input_processing")
    with pytest.raises(ValidationError, match="physical execution assignment"):
        ExecutionGraph(
            graph_id="graph-hidden-physical-field",
            workload_id="wl-1",
            nodes=[node],
            entry_nodes=["input"],
            terminal_nodes=["input"],
            metadata={"nested": {"hardware_assignments": {"input": "gpu-1"}}},
        )

    with pytest.raises(ValidationError, match="physical execution assignment"):
        GraphNode(
            node_id="hidden-model",
            name="Hidden model",
            node_type="input",
            capability_required="input_processing",
            metadata={"model_assignments": {"hidden-model": "model-1"}},
        )


def test_execution_graph_contract_rejects_set_like_metadata_values():
    GraphNode = load("mercury.contracts.execution_graph", "GraphNode")

    with pytest.raises(ValidationError, match="set-like"):
        GraphNode(
            node_id="set-metadata",
            name="Set metadata",
            node_type="input",
            capability_required="input_processing",
            metadata={"tags": {"logical"}},
        )


def test_execution_graph_contract_rejects_invalid_references_cycles_and_mutation():
    ExecutionGraph = load("mercury.contracts.execution_graph", "ExecutionGraph")
    GraphNode = load("mercury.contracts.execution_graph", "GraphNode")
    GraphEdge = load("mercury.contracts.execution_graph", "GraphEdge")

    node_a = GraphNode(
        node_id="a",
        name="A",
        node_type="input",
        capability_required="input_processing",
        metadata={"constraints": {"labels": ["logical-only"]}},
    )
    node_b = GraphNode(node_id="b", name="B", node_type="output", capability_required="output_generation")

    with pytest.raises(ValidationError):
        ExecutionGraph(
            graph_id="graph-invalid-reference",
            workload_id="wl-1",
            nodes=[node_a],
            entry_nodes=["missing"],
            terminal_nodes=["a"],
        )

    with pytest.raises(ValidationError):
        ExecutionGraph(
            graph_id="graph-cycle",
            workload_id="wl-1",
            nodes=[node_a, node_b],
            edges=[
                GraphEdge(edge_id="a-b", source_node="a", target_node="b", edge_type="data"),
                GraphEdge(edge_id="b-a", source_node="b", target_node="a", edge_type="data"),
            ],
            entry_nodes=["a"],
            terminal_nodes=["b"],
        )

    graph = ExecutionGraph(
        graph_id="graph-frozen",
        workload_id="wl-1",
        nodes=[node_a],
        entry_nodes=["a"],
        terminal_nodes=["a"],
        metadata={"provenance": {"sources": ["spec"]}},
    )
    with pytest.raises(ValidationError):
        graph.graph_id = "different-graph"
    with pytest.raises(AttributeError):
        graph.edges.append(
            GraphEdge(edge_id="self-cycle", source_node="a", target_node="a", edge_type="data")
        )
    with pytest.raises(AttributeError):
        graph.entry_nodes.append("a")
    with pytest.raises(TypeError):
        graph.metadata["physical-placement"] = "forbidden"
    with pytest.raises(TypeError):
        node_a.metadata["placement"] = "forbidden"
    assert graph.metadata["provenance"]["sources"] == ("spec",)
    assert node_a.metadata["constraints"]["labels"] == ("logical-only",)
    with pytest.raises(AttributeError):
        graph.metadata["provenance"]["sources"].append("runtime")
