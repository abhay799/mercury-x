from mercury.hardware_personality.contracts import HardwarePersonalityProfile, HardwareTrustState
from mercury.topology.contracts import TopologyNode, make_topology_node_id

def node_from_hardware_profile(profile: HardwarePersonalityProfile, **locality):
    if profile.trust_state is not HardwareTrustState.VERIFIED:
        raise ValueError("topology node requires VERIFIED hardware profile")
    return TopologyNode(
        topology_node_id=make_topology_node_id(profile.hardware_profile_id),
        hardware_profile_id=profile.hardware_profile_id,
        **locality,
    )
