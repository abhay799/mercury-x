from typing import Protocol
from pydantic import Field, model_validator
from mercury.contracts.base import ContractModel
from mercury.reasoning_budget.contracts import BudgetCalibrationState, canonical_hash
from mercury.reasoning_budget.cost import ReasoningBackendKind

class QualityGainEstimate(ContractModel):
    estimate_id: str
    gain_low: float | None = None
    gain_high: float | None = None
    uncertainty: float
    valid: bool
    calibration_state: BudgetCalibrationState = BudgetCalibrationState.UNCALIBRATED
    evidence_ids: tuple[str,...]=()
    backend_id: str
    backend_version: str
    backend_kind: ReasoningBackendKind
    operating_domain: str
    calibration_artifact_id: str | None = None

    @model_validator(mode="after")
    def calibrated_evidence(self):
        if self.calibration_state is BudgetCalibrationState.EMPIRICALLY_CALIBRATED and (not self.calibration_artifact_id or not self.evidence_ids):
            raise ValueError("calibration requires artifact and evidence")
        return self

class QualityGainBackend(Protocol):
    def estimate(self, *, difficulty, extra_compute_units:float, evidence_ids:tuple[str,...]) -> QualityGainEstimate: ...

class EmpiricalQualityGainBackend(QualityGainBackend, Protocol): ...
class LearnedQualityGainBackend(QualityGainBackend, Protocol): ...

class DeterministicQualityGainBackend:
    backend_id="deterministic-quality-gain"; backend_version="v1"
    def estimate(self, *, difficulty, extra_compute_units, evidence_ids=()):
        if difficulty == "UNKNOWN" or not evidence_ids:
            return QualityGainEstimate(
                estimate_id=canonical_hash({"difficulty":str(difficulty),"compute":extra_compute_units,"valid":False}),
                uncertainty=1.0, valid=False, evidence_ids=tuple(sorted(evidence_ids)),
                backend_id=self.backend_id, backend_version=self.backend_version,
                backend_kind=ReasoningBackendKind.DETERMINISTIC, operating_domain="structural-quality-gain")
        # Structural estimate only: an uncalibrated bounded range, never a probability claim.
        upper=min(.25, max(0.0, extra_compute_units)*.01)
        return QualityGainEstimate(
            estimate_id=canonical_hash({"difficulty":str(difficulty),"compute":extra_compute_units,"evidence":sorted(evidence_ids)}),
            gain_low=0.0,gain_high=round(upper,6),uncertainty=.75,valid=True,evidence_ids=tuple(sorted(evidence_ids)),
            backend_id=self.backend_id,backend_version=self.backend_version,
            backend_kind=ReasoningBackendKind.DETERMINISTIC,operating_domain="structural-quality-gain")
