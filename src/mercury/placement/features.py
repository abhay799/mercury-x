from mercury.placement.contracts import PlacementFeatures
from mercury.topology.locality import classify_locality
from mercury.topology.contracts import LocalityDomain

_LOCALITY={LocalityDomain.DEVICE:1.0,LocalityDomain.HOST:.95,LocalityDomain.RACK:.8,
LocalityDomain.ZONE:.65,LocalityDomain.REGION:.5,LocalityDomain.PROVIDER:.3,LocalityDomain.UNKNOWN:0.0}

def extract_features(candidate, *, source_node, target_node, evidence_known=True):
    return PlacementFeatures(
        candidate_id=candidate.candidate_id,
        compatibility_score=1.0 if candidate.eligible else 0.0,
        locality_score=_LOCALITY[classify_locality(source_node,target_node)],
        evidence_score=1.0 if evidence_known else 0.0,
        uncertainty_penalty=0.0 if evidence_known else 1.0,
    )
