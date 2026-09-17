import pytest

from mercury.disaggregated_execution.contracts import ExecutionSegmentState
from mercury.disaggregated_execution.readiness import transition_segment_state
from mercury.hardware_personality.contracts import HardwareRequirement, HardwareTrustState
from mercury.hardware_personality.lifecycle import transition_hardware_trust
from mercury.placement.candidates import generate_typed_candidates
from mercury.placement.features import extract_typed_features
from mercury.placement.predictor import predict_placements
from mercury.topology.paths import build_path_result
from mercury.speculation.planner import build_speculation_plan
from mercury.topology.contracts import TopologyNode
from mercury.topology.graph import build_topology_graph
from mercury.topology.integration import node_from_hardware_profile
from tests._phase12_helpers import make_segment
from tests._phase13_helpers import profile


def _typed_flow():
    segment = make_segment()
    hardware_profile = profile()
    topology_node = node_from_hardware_profile(hardware_profile)
    topology_graph = build_topology_graph(nodes=(topology_node,), links=())
    candidates = generate_typed_candidates(
        segment=segment,
        segments=(segment,),
        handoffs=(),
        requirement=HardwareRequirement(requirement_id="placement-requirement"),
        topology_graph=topology_graph,
        source_node_id=topology_node.topology_node_id,
        profiles_by_node={topology_node.topology_node_id: hardware_profile},
    )
    path_result = build_path_result(
        topology_graph, topology_node.topology_node_id, topology_node.topology_node_id
    )
    features = extract_typed_features(candidates[0], path_result=path_result)
    predictions = predict_placements(candidates, {candidates[0].candidate_id: features})
    ready_segment = transition_segment_state(segment, ExecutionSegmentState.READY)
    plan = build_speculation_plan(
        source_segment=ready_segment,
        placement_candidates=candidates,
        placement_predictions=predictions,
        path_results=(path_result,),
        max_branches=1,
    )
    return segment, hardware_profile, topology_graph, candidates, plan


def test_typed_phase12_through_phase16_preserves_identity_generation_and_fingerprints():
    segment, hardware_profile, topology_graph, candidates, plan = _typed_flow()
    candidate = candidates[0]
    assert candidate.segment_id == segment.segment_id
    assert candidate.hardware_profile_id == hardware_profile.hardware_profile_id
    assert candidate.hardware_profile_generation == hardware_profile.profile_generation
    assert candidate.hardware_profile_fingerprint == hardware_profile.profile_fingerprint
    assert candidate.topology_graph_id == topology_graph.topology_graph_id
    assert candidate.topology_generation == topology_graph.generation
    path_result = build_path_result(
        topology_graph, topology_graph.nodes[0].topology_node_id, candidate.topology_node_id
    )
    requirement = HardwareRequirement(requirement_id="placement-requirement")
    features = extract_typed_features(
        candidate, path_result=path_result, topology_graph=topology_graph,
        hardware_profile=hardware_profile, requirement=requirement,
    )
    assert features.hardware_profile_generation == hardware_profile.profile_generation
    assert features.topology_generation == topology_graph.generation
    assert features.path_bandwidth_bytes_per_s is None
    assert features.uncertainty_penalty == 1.0
    predictions = predict_placements(candidates, {candidate.candidate_id: features})
    ready_segment = transition_segment_state(segment, ExecutionSegmentState.READY)
    typed_plan = build_speculation_plan(
        source_segment=ready_segment, placement_candidates=candidates,
        placement_predictions=predictions, path_results=(path_result,), max_branches=1,
    )
    assert typed_plan.upstream_provenance[0].hardware_profile_generation == hardware_profile.profile_generation
    assert typed_plan.upstream_provenance[0].path_result_id == path_result.path_result_id
    assert typed_plan.upstream_provenance[0].prediction_id == predictions[0].prediction_id
    assert plan.source_segment_id == segment.segment_id
    assert plan.placement_candidate_ids == (candidate.candidate_id,)


def test_typed_flow_fails_closed_at_hardware_topology_and_speculation_boundaries():
    segment, hardware_profile, topology_graph, candidates, _ = _typed_flow()
    stale = transition_hardware_trust(hardware_profile, HardwareTrustState.STALE)
    assert generate_typed_candidates(
        segment=segment,
        segments=(segment,),
        handoffs=(),
        requirement=HardwareRequirement(requirement_id="placement-requirement"),
        topology_graph=topology_graph,
        source_node_id=topology_graph.nodes[0].topology_node_id,
        profiles_by_node={topology_graph.nodes[0].topology_node_id: stale},
    ) == ()

    inactive_node = TopologyNode(**(topology_graph.nodes[0].model_dump() | {"active": False}))
    inactive_graph = build_topology_graph(nodes=(inactive_node,), links=())
    with pytest.raises(ValueError, match="active source"):
        generate_typed_candidates(
            segment=segment,
            segments=(segment,),
            handoffs=(),
            requirement=HardwareRequirement(requirement_id="placement-requirement"),
            topology_graph=inactive_graph,
            source_node_id=inactive_node.topology_node_id,
            profiles_by_node={inactive_node.topology_node_id: hardware_profile},
        )

    ready_segment = transition_segment_state(segment, ExecutionSegmentState.READY)
    with pytest.raises(ValueError, match="eligible"):
        build_speculation_plan(
            source_segment=ready_segment,
            placement_candidates=(candidates[0].model_copy(update={"eligible": False}),),
            max_branches=1,
        )
