"""Behavioral certification checks for the bounded Phase 15 baseline."""

from mercury.placement.backend import DeterministicPlacementBackend, EmpiricalPlacementBackend, LearnedPlacementBackend
from mercury.placement.contracts import (
    PlacementBackendKind, PlacementBackendResult, PlacementCalibrationState,
    PlacementCandidate, PlacementFeatures, PlacementSupportState,
)
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


def typed_provenance():
    try:
        PlacementCandidate(
            candidate_id="candidate", segment_id="segment", topology_node_id="node",
            hardware_profile_id="profile", eligible=True, topology_graph_id="graph",
        )
    except ValueError:
        return True, "partial typed placement provenance is rejected"
    return False, "partial typed placement provenance was accepted"


def feature_provenance():
    features = PlacementFeatures(
        candidate_id="candidate", compatibility_score=1, locality_score=0,
        evidence_score=0, uncertainty_penalty=1, hardware_profile_id="profile",
        hardware_profile_generation=1, topology_graph_id="graph", topology_generation=1,
        evidence_ids=(),
    )
    return features.path_bandwidth_bytes_per_s is None and features.uncertainty_penalty == 1, "unknown path evidence remains explicit and penalized"


def backend_identity():
    class Backend:
        backend_id = "fixture-backend"
        backend_version = "v1"
        def score(self, features):
            return 0.5
    prediction = predict_placements((_candidate(),), {"candidate": _features("candidate")}, backend=Backend())[0]
    return prediction.backend_id == "fixture-backend" and prediction.backend_version == "v1", "backend identity and version are preserved"


def score_bounds():
    class InvalidBackend:
        backend_id = "invalid"
        backend_version = "v1"
        def score(self, features):
            return 2.0
    try:
        predict_placements((_candidate(),), {"candidate": _features("candidate")}, backend=InvalidBackend())
    except ValueError:
        return True, "unbounded backend output is rejected"
    return False, "unbounded backend output was accepted"


def no_execution():
    candidate, features = _candidate(), _features("candidate")
    before = (candidate.model_dump(), features.model_dump())
    predict_placements((candidate,), {candidate.candidate_id: features})
    return before == (candidate.model_dump(), features.model_dump()), "prediction is side-effect-free over inputs"


def explicit_backend_contracts():
    result = DeterministicPlacementBackend().predict(_features("candidate"))
    calibrated_rejected = False
    try:
        PlacementBackendResult(
            backend_id="empirical", backend_version="v1", backend_kind=PlacementBackendKind.EMPIRICAL,
            candidate_id="candidate", score=.5, uncertainty=.2,
            calibration_state=PlacementCalibrationState.EMPIRICALLY_CALIBRATED,
            operating_domain="fixture",
        )
    except ValueError:
        calibrated_rejected = True
    return result.backend_kind is PlacementBackendKind.DETERMINISTIC and EmpiricalPlacementBackend is not LearnedPlacementBackend and calibrated_rejected, "deterministic output is typed; empirical/learned interfaces exist; dishonest calibration rejects"


def feature_completeness():
    features = _features("candidate")
    return all(getattr(features, name) is PlacementSupportState.UNKNOWN for name in (
        "memory_support", "precision_support", "runtime_support", "software_stack_support"
    )) and features.path_bandwidth_bytes_per_s is None and features.topology_uncertainty == 1, "hard feature dimensions preserve explicit UNKNOWN rather than attractive zeroes"


CHECKS = {
    "contracts": contracts,
    "determinism": determinism,
    "uncalibrated": uncalibrated,
    "eligibility": eligibility,
    "typed_provenance": typed_provenance,
    "feature_provenance": feature_provenance,
    "backend_identity": backend_identity,
    "score_bounds": score_bounds,
    "no_execution": no_execution,
    "explicit_backend_contracts": explicit_backend_contracts,
    "feature_completeness": feature_completeness,
}
