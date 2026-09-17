from mercury.hardware_personality.compatibility import evaluate_hardware_compatibility
from mercury.hardware_personality.contracts import HardwareCompatibilityState
from mercury.placement.contracts import PlacementCandidate, stable_hash

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
