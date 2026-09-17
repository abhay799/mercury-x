from mercury.placement.backend import DeterministicPlacementBackend
from mercury.placement.contracts import PlacementPrediction,PlacementConfidenceBand,PlacementCalibrationState,stable_hash

def predict_placements(candidates, features_by_id, backend=None):
    backend=backend or DeterministicPlacementBackend()
    out=[]
    for c in candidates:
        if not c.eligible: continue
        f=features_by_id[c.candidate_id]; s=backend.score(f)
        if not isinstance(s, (int, float)) or isinstance(s, bool) or not 0.0 <= float(s) <= 1.0:
            raise ValueError("placement backend score must be bounded between zero and one")
        s = float(s)
        band=PlacementConfidenceBand.HIGH if s>=.75 else PlacementConfidenceBand.MEDIUM if s>=.45 else PlacementConfidenceBand.LOW
        pid=stable_hash({"candidate_id":c.candidate_id,"score":s})
        out.append(PlacementPrediction(prediction_id=pid,candidate_id=c.candidate_id,
            raw_score=s,confidence_band=band,calibration_state=PlacementCalibrationState.UNCALIBRATED,
            reason_codes=("DETERMINISTIC_BASELINE",),
            backend_id=getattr(backend, "backend_id", "external-unidentified"),
            backend_version=getattr(backend, "backend_version", "unknown")))
    return tuple(sorted(out,key=lambda x:(-x.raw_score,x.candidate_id)))
