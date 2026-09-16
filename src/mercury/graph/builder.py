"""Deterministic construction of logical execution graphs from Phase 2 output."""

from __future__ import annotations

from mercury.graph.models import (
    ExecutionGraph,
    ExecutionGraphEdge,
    ExecutionGraphNode,
    GraphDependencyType,
    GraphNodeType,
)
from mercury.intelligence.calibration import CalibrationStatus
from mercury.intelligence.models import ComputationalCapability, Evidence, ReasoningComplexity, WorkloadModality
from mercury.intelligence.pipeline import PipelineStatus, WorkloadIntelligencePipelineResult


def _node(
    node_id: str,
    node_type: GraphNodeType,
    capability: ComputationalCapability,
    reason: str,
) -> ExecutionGraphNode:
    return ExecutionGraphNode(
        node_id=node_id,
        node_type=node_type,
        purpose=f"logical {node_type.value} stage",
        required_capabilities=(capability,),
        evidence=(Evidence("phase2.intelligence", reason),),
    )


def _require_valid_pipeline(
    result: WorkloadIntelligencePipelineResult,
) -> None:
    if not isinstance(result, WorkloadIntelligencePipelineResult):
        raise ValueError("pipeline result must be a WorkloadIntelligencePipelineResult")
    if result.status not in (PipelineStatus.PASS, PipelineStatus.DEGRADED):
        raise ValueError("pipeline status must be PASS or DEGRADED")
    if result.signals is None or result.profile is None or result.calibration is None:
        raise ValueError("pipeline result must contain every Phase 2 stage")
    if result.calibration.status not in (CalibrationStatus.PASS, CalibrationStatus.DEGRADED):
        raise ValueError("calibration status must be PASS or DEGRADED")
    identity = (result.request_id, result.workload_id, result.session_id)
    if any(not isinstance(value, str) or not value.strip() for value in identity):
        raise ValueError("pipeline identity must be nonblank")
    for stage in (result.signals, result.profile, result.calibration.profile):
        if (stage.request_id, stage.workload_id, stage.session_id) != identity:
            raise ValueError("Phase 2 identity does not match pipeline identity")
    if result.calibration.profile is not result.profile:
        raise ValueError("calibration must preserve the intelligence profile")


def _capability(
    capabilities: tuple[ComputationalCapability, ...], preferred: ComputationalCapability
) -> ComputationalCapability:
    return preferred if preferred in capabilities else capabilities[0]


def build_execution_graph(
    result: WorkloadIntelligencePipelineResult,
) -> ExecutionGraph:
    """Build a logical DAG from certified Phase 2 intelligence only."""
    _require_valid_pipeline(result)
    assert result.profile is not None
    profile = result.profile
    capabilities = profile.required_capabilities
    if not capabilities or any(not isinstance(item, ComputationalCapability) for item in capabilities):
        raise ValueError("required capability state is unsupported")
    if len(profile.modalities) != 1:
        raise ValueError("workload modality state is unsupported")
    modality = profile.modalities[0]
    if not isinstance(modality, WorkloadModality):
        raise ValueError("workload modality is unsupported")

    nodes: list[ExecutionGraphNode] = []
    processing_added = False
    default_capability = capabilities[0]
    nodes.append(_node("node-input", GraphNodeType.INPUT, default_capability, "Phase 2 workload input requires a logical input stage"))

    visual = modality in (WorkloadModality.IMAGE, WorkloadModality.VIDEO, WorkloadModality.MULTIMODAL)
    audible = modality in (WorkloadModality.AUDIO, WorkloadModality.MULTIMODAL)
    if visual or audible:
        capability = _capability(
            capabilities,
            ComputationalCapability.VISION if visual else ComputationalCapability.SPEECH,
        )
        nodes.append(_node("node-preprocess-1", GraphNodeType.PREPROCESS, capability, "Phase 2 modality requires explicit logical preprocessing"))
        processing_added = True
    if modality is WorkloadModality.STRUCTURED_DATA:
        nodes.append(_node("node-transform-1", GraphNodeType.TRANSFORM, _capability(capabilities, ComputationalCapability.STRUCTURED_OUTPUT), "Phase 2 structured-data modality requires logical transformation"))
        processing_added = True
    if ComputationalCapability.RETRIEVAL in capabilities:
        nodes.append(_node("node-retrieval-1", GraphNodeType.RETRIEVAL, ComputationalCapability.RETRIEVAL, "Phase 2 retrieval capability requires a logical retrieval stage"))
        processing_added = True
    if ComputationalCapability.TOOL_USE in capabilities or ComputationalCapability.CODE_EXECUTION in capabilities:
        tool_capability = _capability(capabilities, ComputationalCapability.CODE_EXECUTION)
        nodes.append(_node("node-tool-1", GraphNodeType.TOOL, tool_capability, "Phase 2 tool or code-execution capability requires a logical tool stage"))
        processing_added = True
    reasoning_count = 0
    if profile.reasoning_complexity in (ReasoningComplexity.HIGH, ReasoningComplexity.DEEP):
        reasoning_count = 2
    elif ComputationalCapability.REASONING in capabilities:
        reasoning_count = 1
    for index in range(1, reasoning_count + 1):
        nodes.append(_node(f"node-reasoning-{index}", GraphNodeType.REASONING, _capability(capabilities, ComputationalCapability.REASONING), "Phase 2 reasoning complexity requires a bounded logical reasoning stage"))
        processing_added = True
    if not processing_added:
        nodes.append(_node("node-transform-1", GraphNodeType.TRANSFORM, default_capability, "Phase 2 workload requires one conservative logical processing stage"))
    if ComputationalCapability.STRUCTURED_OUTPUT in capabilities and modality is not WorkloadModality.STRUCTURED_DATA:
        nodes.append(_node("node-validation-1", GraphNodeType.VALIDATION, ComputationalCapability.STRUCTURED_OUTPUT, "Phase 2 structured-output capability requires logical validation before output"))
    nodes.append(_node("node-z-output", GraphNodeType.OUTPUT, _capability(capabilities, ComputationalCapability.GENERATION), "Phase 2 workload requires a logical output stage"))

    edges = tuple(
        ExecutionGraphEdge(
            source_node_id=nodes[index].node_id,
            target_node_id=nodes[index + 1].node_id,
            dependency_type=(
                GraphDependencyType.TOOL_RESULT
                if nodes[index].node_type is GraphNodeType.TOOL
                else GraphDependencyType.DATA
            ),
            evidence=(Evidence("phase2.intelligence", "logical data dependency follows deterministic stage order"),),
        )
        for index in range(len(nodes) - 1)
    )
    return ExecutionGraph(
        graph_id=f"graph-{result.request_id}",
        request_id=result.request_id,
        workload_id=result.workload_id,
        session_id=result.session_id,
        nodes=tuple(nodes),
        edges=edges,
        provenance=profile.evidence,
        intelligence_profile=profile,
    )
