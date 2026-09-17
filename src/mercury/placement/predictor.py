from mercury.placement.backend import DeterministicPlacementBackend
from mercury.placement.contracts import PlacementPrediction,PlacementConfidenceBand,PlacementCalibrationState,stable_hash

def predict_placements(candidates, features_by_id, backend=None):
    backend=backend or DeterministicPlacementBackend()
    out=[]
    for c in candidates:
        if not c.eligible: continue
        f=features_by_id[c.candidate_id]; s=backend.score(f)
        band=PlacementConfidenceBand.HIGH if s>=.75 else PlacementConfidenceBand.MEDIUM if s>=.45 else PlacementConfidenceBand.LOW
        pid=stable_hash({"candidate_id":c.candidate_id,"score":s})
        out.append(PlacementPrediction(prediction_id=pid,candidate_id=c.candidate_id,
            raw_score=s,confidence_band=band,calibration_state=PlacementCalibrationState.UNCALIBRATED,
            reason_codes=("DETERMINISTIC_BASELINE",)))
    return tuple(sorted(out,key=lambda x:(-x.raw_score,x.candidate_id)))
