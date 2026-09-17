from mercury.placement.contracts import *
from mercury.placement.predictor import predict_placements
def test_placement_prediction_is_deterministic_and_uncalibrated():
    c=PlacementCandidate(candidate_id="c",segment_id="s",topology_node_id="n",hardware_profile_id="p",eligible=True)
    f=PlacementFeatures(candidate_id="c",compatibility_score=1,locality_score=.5,evidence_score=1,uncertainty_penalty=0)
    a=predict_placements((c,),{"c":f}); b=predict_placements((c,),{"c":f})
    assert a==b
    assert a[0].calibration_state is PlacementCalibrationState.UNCALIBRATED
