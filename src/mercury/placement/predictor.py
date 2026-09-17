from mercury.placement.backend import DeterministicPlacementBackend
from mercury.placement.contracts import PlacementBackendKind, PlacementBackendResult, PlacementPrediction,PlacementConfidenceBand,PlacementCalibrationState,stable_hash

def predict_placements(candidates, features_by_id, backend=None):
    backend=backend or DeterministicPlacementBackend()
    out=[]
    for c in candidates:
        if not c.eligible: continue
        f=features_by_id[c.candidate_id]
        if f.candidate_id != c.candidate_id:
            raise ValueError("placement feature candidate mismatch")
        if hasattr(backend, "predict"):
            backend_result = backend.predict(f)
            if type(backend_result) is not PlacementBackendResult:
                raise ValueError("placement backend must return typed result")
            backend_result = PlacementBackendResult.model_validate(backend_result.model_dump())
        else:
            score = backend.score(f)
            if not isinstance(score, (int, float)) or isinstance(score, bool) or not 0.0 <= float(score) <= 1.0:
                raise ValueError("placement backend score must be bounded between zero and one")
            backend_result = PlacementBackendResult(
                backend_id=getattr(backend, "backend_id", "external-unidentified"),
                backend_version=getattr(backend, "backend_version", "unknown"),
                backend_kind=PlacementBackendKind.EMPIRICAL, candidate_id=c.candidate_id,
                score=float(score), uncertainty=1.0,
                calibration_state=PlacementCalibrationState.UNCALIBRATED,
                operating_domain="legacy-external-uncalibrated",
                hardware_profile_generation=f.hardware_profile_generation,
                topology_generation=f.topology_generation,
            )
        if backend_result.candidate_id != c.candidate_id:
            raise ValueError("placement backend candidate mismatch")
        if backend_result.hardware_profile_generation != f.hardware_profile_generation or backend_result.topology_generation != f.topology_generation:
            raise ValueError("placement backend provenance generation mismatch")
        s=backend_result.score
        if not isinstance(s, (int, float)) or isinstance(s, bool) or not 0.0 <= float(s) <= 1.0:
            raise ValueError("placement backend score must be bounded between zero and one")
        s = float(s)
        band=PlacementConfidenceBand.HIGH if s>=.75 else PlacementConfidenceBand.MEDIUM if s>=.45 else PlacementConfidenceBand.LOW
        pid=stable_hash({"backend_result":backend_result.model_dump(mode="json")})
        out.append(PlacementPrediction(prediction_id=pid,candidate_id=c.candidate_id,
            raw_score=s,confidence_band=band,calibration_state=PlacementCalibrationState.UNCALIBRATED,
            reason_codes=("DETERMINISTIC_BASELINE",),
            backend_id=backend_result.backend_id, backend_version=backend_result.backend_version,
            backend_kind=backend_result.backend_kind, uncertainty=backend_result.uncertainty,
            calibration_artifact_id=backend_result.calibration_artifact_id,
            calibration_dataset_id=backend_result.calibration_dataset_id,
            evidence_ids=backend_result.evidence_ids, operating_domain=backend_result.operating_domain,
            artifact_version=backend_result.artifact_version,
            hardware_profile_generation=backend_result.hardware_profile_generation,
            topology_generation=backend_result.topology_generation))
    return tuple(sorted(out,key=lambda x:x.candidate_id))
