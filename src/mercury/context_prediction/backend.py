"""Replaceable CPU-only prediction boundary; baseline scores are uncalibrated."""
from typing import Protocol, runtime_checkable

from pydantic import Field, field_validator, model_validator

from mercury.contracts.base import ContractModel
from mercury.context_prediction.contracts import (
    ContextPredictionCandidate, ContextPredictionFeatureVector, ContextPredictionHorizon,
    ContextConfidenceBand, ContextPredictionReasonCode, ContextCalibrationStatus,
    MAX_REASON_CODES,
)
from mercury.context_prediction.scoring import score_prediction


class ScoredContextPrediction(ContractModel):
    candidate_id: str
    prediction_horizon: ContextPredictionHorizon
    raw_score: float = Field(ge=0, le=1)
    confidence_band: ContextConfidenceBand
    reason_codes: tuple[ContextPredictionReasonCode, ...]
    calibration_status: ContextCalibrationStatus = ContextCalibrationStatus.UNCALIBRATED
    calibration_evidence: tuple[str, ...] = ()

    @field_validator("candidate_id")
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError("candidate identity required")
        return value

    @model_validator(mode="after")
    def baseline_metadata(self):
        if self.calibration_status is not ContextCalibrationStatus.UNCALIBRATED or self.calibration_evidence:
            raise ValueError("baseline backend cannot claim empirical calibration")
        if not self.reason_codes or len(self.reason_codes) > MAX_REASON_CODES:
            raise ValueError("bounded nonempty reasons required")
        if self.reason_codes != tuple(sorted(set(self.reason_codes), key=lambda x: x.value)):
            raise ValueError("canonical reasons required")
        expected = (ContextConfidenceBand.LOW if self.raw_score < 0.4 else
                    ContextConfidenceBand.MEDIUM if self.raw_score < 0.75 else ContextConfidenceBand.HIGH)
        if self.confidence_band is not expected:
            raise ValueError("backend confidence band mismatch")
        return self


@runtime_checkable
class ContextPredictionBackend(Protocol):
    def predict(
        self,
        features: tuple[ContextPredictionFeatureVector, ...],
        candidates: tuple[ContextPredictionCandidate, ...],
        horizon: ContextPredictionHorizon | None = None,
    ) -> tuple[ScoredContextPrediction, ...]: ...


class DeterministicWeightedPredictionBackend:
    """Transparent fixed weights, not learned parameters or probabilities."""
    def predict(self, features, candidates, horizon=None):
        feature_by_id = {item.candidate_id: item for item in features}
        if len(feature_by_id) != len(features) or set(feature_by_id) != {c.candidate_id for c in candidates}:
            raise ValueError("backend candidate/feature identities must match")
        results = []
        for candidate in candidates:
            selected_horizon, score, band, reasons = score_prediction(feature_by_id[candidate.candidate_id])
            if horizon is None or selected_horizon is horizon:
                results.append(ScoredContextPrediction(candidate_id=candidate.candidate_id,
                    prediction_horizon=selected_horizon, raw_score=score,
                    confidence_band=band, reason_codes=reasons))
        return tuple(results)
