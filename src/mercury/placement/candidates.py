from mercury.hardware_personality.compatibility import evaluate_hardware_compatibility
from mercury.hardware_personality.contracts import HardwareCompatibilityState
from mercury.placement.contracts import PlacementCandidate, stable_hash
from mercury.disaggregated_execution.contracts import ExecutionSegment
from mercury.disaggregated_execution.readiness import evaluate_segment_readiness
from mercury.hardware_personality.contracts import HardwarePersonalityProfile
from mercury.topology.contracts import TopologyGraph, TopologyCapabilityState
from mercury.topology.paths import build_path_result, path_capability

def generate_candidates(*, segment, requirement, profiles_by_node):
    out=[]
    for node_id,profile in sorted(profiles_by_node.items()):
        comp=evaluate_hardware_compatibility(profile,requirement)
        eligible=comp.state is HardwareCompatibilityState.COMPATIBLE
        reasons=comp.reason_codes if not eligible else ("HARD_REQUIREMENTS_SATISFIED",)
        cid=stable_hash({"segment_id":segment.segment_id,"node_id":node_id,"profile":profile.hardware_profile_id})
        out.append(PlacementCandidate(candidate_id=cid,segment_id=segment.segment_id,
            topology_node_id=node_id,hardware_profile_id=profile.hardware_profile_id,
            eligible=eligible,reason_codes=tuple(sorted(reasons))))
    return tuple(out)


def generate_typed_candidates(
    *, segment, segments, handoffs, requirement, topology_graph, source_node_id, profiles_by_node
):
    """Produce only hard-eligible candidates from typed Phase 12–14 artifacts."""
    if type(segment) is not ExecutionSegment:
        raise ValueError("Phase 12 ExecutionSegment required")
    if type(topology_graph) is not TopologyGraph:
        raise ValueError("Phase 14 TopologyGraph required")
    if not evaluate_segment_readiness(segment, segments=segments, handoffs=handoffs):
        raise ValueError("Phase 12 segment is not ready")
    nodes = {node.topology_node_id: node for node in topology_graph.nodes}
    if source_node_id not in nodes or not nodes[source_node_id].active:
        raise ValueError("active source topology node required")
    candidates = []
    for node_id, profile in sorted(profiles_by_node.items()):
        if type(profile) is not HardwarePersonalityProfile:
            raise ValueError("typed HardwarePersonalityProfile required")
        node = nodes.get(node_id)
        if node is None or not node.active or node.hardware_profile_id != profile.hardware_profile_id:
            continue
        compatibility = evaluate_hardware_compatibility(profile, requirement)
        if compatibility.state is not HardwareCompatibilityState.COMPATIBLE:
            continue
        if path_capability(topology_graph, source_node_id, node_id) is not TopologyCapabilityState.AVAILABLE:
            continue
        path_result = build_path_result(topology_graph, source_node_id, node_id)
        evidence_ids = path_result.metric_evidence_ids
        candidate_id = stable_hash({
            "segment_id": segment.segment_id,
            "topology_graph_id": topology_graph.topology_graph_id,
            "topology_generation": topology_graph.generation,
            "node_id": node_id,
            "hardware_profile_id": profile.hardware_profile_id,
            "hardware_profile_generation": profile.profile_generation,
            "hardware_profile_fingerprint": profile.profile_fingerprint,
            "path_result_id": path_result.path_result_id,
            "path_result_fingerprint": path_result.fingerprint,
        })
        candidates.append(PlacementCandidate(
            candidate_id=candidate_id,
            segment_id=segment.segment_id,
            topology_node_id=node_id,
            hardware_profile_id=profile.hardware_profile_id,
            eligible=True,
            reason_codes=("HARD_REQUIREMENTS_SATISFIED",),
            topology_graph_id=topology_graph.topology_graph_id,
            topology_generation=topology_graph.generation,
            hardware_profile_generation=profile.profile_generation,
            hardware_profile_fingerprint=profile.profile_fingerprint,
            path_result_id=path_result.path_result_id,
            path_result_fingerprint=path_result.fingerprint,
            evidence_ids=evidence_ids,
        ))
    return tuple(candidates)
