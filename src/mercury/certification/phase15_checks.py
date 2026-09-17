"""Behavioral certification checks for the bounded Phase 15 baseline."""

from mercury.placement.contracts import PlacementCalibrationState, PlacementCandidate, PlacementFeatures
from mercury.placement.predictor import predict_placements


def _candidate(candidate_id="candidate", *, eligible=True):
    return PlacementCandidate(candidate_id=candidate_id, segment_id="segment", topology_node_id="node", hardware_profile_id="profile", eligible=eligible, reason_codes=("HARD_REQUIREMENTS_SATISFIED",))


def _features(candidate_id):
    return PlacementFeatures(candidate_id=candidate_id, compatibility_score=1.0, locality_score=0.5, evidence_score=1.0, uncertainty_penalty=0.0)


def contracts():
    try:
        _candidate(" ")
    except ValueError:
        return True, "blank placement candidate identity rejected"
    return False, "blank placement candidate identity was accepted"


def determinism():
    first, second = _candidate("a"), _candidate("b")
    values = {first.candidate_id: _features(first.candidate_id), second.candidate_id: _features(second.candidate_id)}
    return predict_placements((first, second), values) == predict_placements((second, first), values), "candidate permutation produces identical prediction ordering"


def uncalibrated():
    prediction = predict_placements((_candidate(),), {"candidate": _features("candidate")})[0]
    return prediction.calibration_state is PlacementCalibrationState.UNCALIBRATED and prediction.backend_id == "deterministic-weighted", "baseline is explicitly uncalibrated with identified backend"


def eligibility():
    denied = _candidate(eligible=False)
    return predict_placements((denied,), {denied.candidate_id: _features(denied.candidate_id)}) == (), "hard-ineligible candidate cannot enter scoring output"


def no_execution():
    candidate, features = _candidate(), _features("candidate")
    before = (candidate.model_dump(), features.model_dump())
    predict_placements((candidate,), {candidate.candidate_id: features})
    return before == (candidate.model_dump(), features.model_dump()), "prediction is side-effect-free over inputs"


CHECKS = {"contracts": contracts, "determinism": determinism, "uncalibrated": uncalibrated, "eligibility": eligibility, "no_execution": no_execution}
