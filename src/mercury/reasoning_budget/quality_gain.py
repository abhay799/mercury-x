from typing import Protocol
from mercury.contracts.base import ContractModel
from mercury.reasoning_budget.contracts import BudgetCalibrationState, canonical_hash

class QualityGainEstimate(ContractModel):
    estimate_id: str
    gain_low: float | None = None
    gain_high: float | None = None
    uncertainty: float
    valid: bool
    calibration_state: BudgetCalibrationState = BudgetCalibrationState.UNCALIBRATED
    evidence_ids: tuple[str,...]=()

class QualityGainBackend(Protocol):
    def estimate(self, *, difficulty, extra_compute_units:float, evidence_ids:tuple[str,...]) -> QualityGainEstimate: ...

class DeterministicQualityGainBackend:
    def estimate(self, *, difficulty, extra_compute_units, evidence_ids=()):
        if difficulty == "UNKNOWN" or not evidence_ids:
            return QualityGainEstimate(
                estimate_id=canonical_hash({"difficulty":str(difficulty),"compute":extra_compute_units,"valid":False}),
                uncertainty=1.0, valid=False, evidence_ids=tuple(sorted(evidence_ids)))
        # Structural estimate only: an uncalibrated bounded range, never a probability claim.
        upper=min(.25, max(0.0, extra_compute_units)*.01)
        return QualityGainEstimate(
            estimate_id=canonical_hash({"difficulty":str(difficulty),"compute":extra_compute_units,"evidence":sorted(evidence_ids)}),
            gain_low=0.0,gain_high=round(upper,6),uncertainty=.75,valid=True,evidence_ids=tuple(sorted(evidence_ids)))
