from typing import Protocol
from mercury.placement.scoring import score_features
from mercury.placement.contracts import (
    PlacementBackendKind, PlacementBackendResult, PlacementCalibrationState,
)

class PlacementBackend(Protocol):
    backend_id: str
    backend_version: str
    def predict(self, features) -> PlacementBackendResult: ...

class EmpiricalPlacementBackend(PlacementBackend, Protocol):
    """Interface only: an implementation must supply real empirical evidence."""

class LearnedPlacementBackend(PlacementBackend, Protocol):
    """Interface only: an implementation must supply a configured learned artifact."""

class DeterministicPlacementBackend:
    backend_id = "deterministic-weighted"
    backend_version = "v1"

    def score(self,features):
        return score_features(features)

    def predict(self, features):
        return PlacementBackendResult(
            backend_id=self.backend_id, backend_version=self.backend_version,
            backend_kind=PlacementBackendKind.DETERMINISTIC,
            candidate_id=features.candidate_id, score=self.score(features), uncertainty=1.0,
            calibration_state=PlacementCalibrationState.UNCALIBRATED,
            evidence_ids=features.evidence_ids, operating_domain="certified-deterministic-baseline",
            hardware_profile_generation=features.hardware_profile_generation,
            topology_generation=features.topology_generation,
        )
