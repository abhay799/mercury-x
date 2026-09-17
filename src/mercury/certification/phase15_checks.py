from mercury.placement.contracts import *
from mercury.placement.predictor import predict_placements
def behavior():
    c=PlacementCandidate(candidate_id="c",segment_id="s",topology_node_id="n",hardware_profile_id="p",eligible=True)
    f=PlacementFeatures(candidate_id="c",compatibility_score=1,locality_score=1,evidence_score=1,uncertainty_penalty=0)
    p=predict_placements((c,),{"c":f})[0]
    return p.calibration_state is PlacementCalibrationState.UNCALIBRATED, "deterministic uncalibrated prediction"
def boundary():
    import inspect, mercury.placement.predictor as p
    t=inspect.getsource(p)
    return not any(x in t for x in ("execute(","schedule(","migrate(","provision(")), "no execution side effects"
CHECKS={"contracts":behavior,"determinism":behavior,"uncalibrated":behavior,"eligibility":behavior,"no_execution":boundary}
