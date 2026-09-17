from mercury.placement.contracts import PlacementFeatures, PlacementSupportState
from mercury.topology.locality import classify_locality
from mercury.topology.contracts import LocalityDomain, TopologyNode
from mercury.topology.contracts import TopologyGraph
from mercury.topology.paths import validate_current_path_result
from mercury.topology.contracts import PathResult, TopologyCapabilityState
from mercury.hardware_personality.contracts import HardwarePersonalityProfile, HardwareRequirement, HardwareTrustState

_LOCALITY={LocalityDomain.DEVICE:1.0,LocalityDomain.HOST:.95,LocalityDomain.RACK:.8,
LocalityDomain.ZONE:.65,LocalityDomain.REGION:.5,LocalityDomain.PROVIDER:.3,LocalityDomain.UNKNOWN:0.0}

def extract_features(candidate, *, source_node, target_node, evidence_known=True):
    if not isinstance(source_node, TopologyNode) or not isinstance(target_node, TopologyNode):
        raise ValueError("placement features require typed TopologyNode inputs")
    if not source_node.active or not target_node.active:
        raise ValueError("placement features require active topology nodes")
    return PlacementFeatures(
        candidate_id=candidate.candidate_id,
        compatibility_score=1.0 if candidate.eligible else 0.0,
        locality_score=_LOCALITY[classify_locality(source_node,target_node)],
        evidence_score=1.0 if evidence_known else 0.0,
        uncertainty_penalty=0.0 if evidence_known else 1.0,
    )


def extract_typed_features(candidate, *, path_result, topology_graph=None, source_node_id=None,
                           hardware_profile=None, requirement=None):
    if not candidate.eligible or candidate.topology_graph_id is None:
        raise ValueError("typed eligible placement candidate required")
    if type(path_result) is not PathResult:
        raise ValueError("typed PathResult required")
    path_result = PathResult.model_validate(path_result.model_dump())
    if topology_graph is not None:
        validate_current_path_result(path_result, topology_graph)
    if (
        candidate.topology_graph_id != path_result.graph_id
        or candidate.topology_generation != path_result.graph_generation
        or candidate.path_result_id != path_result.path_result_id
        or candidate.path_result_fingerprint != path_result.fingerprint
        or candidate.topology_node_id != path_result.destination_node_id
    ):
        raise ValueError("candidate path provenance mismatch")
    if path_result.capability_state is not TopologyCapabilityState.AVAILABLE:
        raise ValueError("candidate topology path unavailable")
    evidence_ids = path_result.metric_evidence_ids
    bandwidth = path_result.measured_bottleneck_bandwidth_bytes_per_s or path_result.declared_bottleneck_bandwidth_bytes_per_s
    latency = path_result.measured_aggregate_latency_us or path_result.declared_aggregate_latency_us
    if (hardware_profile is None) != (requirement is None):
        raise ValueError("hardware profile and requirement must be supplied together")
    memory_headroom = None
    memory_support = precision_support = runtime_support = PlacementSupportState.UNKNOWN
    software_support = PlacementSupportState.UNKNOWN
    if hardware_profile is not None:
        if type(hardware_profile) is not HardwarePersonalityProfile or type(requirement) is not HardwareRequirement:
            raise ValueError("typed hardware profile and requirement required")
        if (
            hardware_profile.hardware_profile_id != candidate.hardware_profile_id
            or hardware_profile.profile_generation != candidate.hardware_profile_generation
            or hardware_profile.profile_fingerprint != candidate.hardware_profile_fingerprint
        ):
            raise ValueError("candidate hardware profile provenance mismatch")
        if requirement.minimum_memory_bytes is not None:
            capacity = hardware_profile.descriptor.memory_capacity_bytes
            if capacity is not None:
                memory_headroom = max(0, capacity - requirement.minimum_memory_bytes)
                memory_support = PlacementSupportState.SUPPORTED if capacity >= requirement.minimum_memory_bytes else PlacementSupportState.UNSUPPORTED
        if requirement.required_precision is not None:
            precision_support = PlacementSupportState.SUPPORTED
        if requirement.required_runtime_capability is not None:
            runtime_support = PlacementSupportState.SUPPORTED
        if hardware_profile.software_stack:
            software_support = PlacementSupportState.SUPPORTED
    provenance = tuple(sorted((
        ("hardware_trust", (candidate.hardware_profile_fingerprint,)),
        ("memory_headroom", (candidate.hardware_profile_fingerprint,)),
        ("precision_support", (candidate.hardware_profile_fingerprint,)),
        ("runtime_support", (candidate.hardware_profile_fingerprint,)),
        ("software_stack_support", (candidate.hardware_profile_fingerprint,)),
        ("path_bandwidth", evidence_ids),
        ("path_latency", evidence_ids),
        ("topology_locality", (path_result.path_result_id,)),
    )))
    return PlacementFeatures(
        candidate_id=candidate.candidate_id,
        compatibility_score=1.0,
        locality_score=_LOCALITY[path_result.locality],
        evidence_score=1.0 if evidence_ids else 0.0,
        uncertainty_penalty=0.0 if evidence_ids else 1.0,
        hardware_profile_id=candidate.hardware_profile_id,
        hardware_profile_generation=candidate.hardware_profile_generation,
        topology_graph_id=path_result.graph_id,
        topology_generation=path_result.graph_generation,
        path_bandwidth_bytes_per_s=bandwidth,
        path_latency_us=latency,
        path_result_id=path_result.path_result_id,
        path_result_fingerprint=path_result.fingerprint,
        memory_headroom_bytes=memory_headroom,
        memory_support=memory_support,
        precision_support=precision_support,
        runtime_support=runtime_support,
        software_stack_support=software_support,
        hardware_trust=PlacementSupportState.SUPPORTED,
        topology_locality=path_result.locality.value,
        path_capability=PlacementSupportState.SUPPORTED,
        topology_uncertainty=0.0 if evidence_ids else 1.0,
        feature_provenance=provenance,
        evidence_ids=evidence_ids,
    )
