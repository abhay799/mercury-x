from enum import Enum
from typing import Protocol
from pydantic import Field, model_validator
from mercury.contracts.base import ContractModel
from mercury.reasoning_budget.contracts import BudgetCalibrationState, canonical_hash

class ReasoningBackendKind(str, Enum):
    DETERMINISTIC="DETERMINISTIC"; EMPIRICAL="EMPIRICAL"; LEARNED="LEARNED"

class ReasoningCostEstimate(ContractModel):
    estimate_id: str
    compute_units: float
    token_units: int
    verification_units: float
    speculation_units: float
    retry_units: float = Field(ge=0)
    aggregation_units: float = Field(ge=0)
    backend_id: str
    backend_version: str
    backend_kind: ReasoningBackendKind
    operating_domain: str
    uncertainty: float = Field(ge=0, le=1)
    calibration_state: BudgetCalibrationState = BudgetCalibrationState.UNCALIBRATED
    calibration_artifact_id: str | None = None
    evidence_ids: tuple[str, ...] = ()

    @model_validator(mode="after")
    def calibration_honesty(self):
        if self.calibration_state is BudgetCalibrationState.EMPIRICALLY_CALIBRATED and (not self.calibration_artifact_id or not self.evidence_ids):
            raise ValueError("calibration requires artifact and evidence")
        if self.calibration_state is BudgetCalibrationState.UNCALIBRATED and self.calibration_artifact_id is not None:
            raise ValueError("uncalibrated cost cannot claim calibration artifact")
        return self

class ReasoningCostBackend(Protocol):
    def estimate(self, **kwargs) -> ReasoningCostEstimate: ...

class EmpiricalReasoningCostBackend(ReasoningCostBackend, Protocol): ...
class LearnedReasoningCostBackend(ReasoningCostBackend, Protocol): ...

class DeterministicReasoningCostBackend:
    backend_id="deterministic-reasoning-cost"; backend_version="v1"
    def estimate(self, *, steps, tokens, verification_depth, speculation_width, retry_attempts=0, aggregation_units=0, evidence_ids=()):
        retry_units=max(0,retry_attempts)*1.0
        compute=round(steps*1.0 + tokens/1024.0 + verification_depth*1.5 + max(0,speculation_width-1)*2.0 + retry_units + aggregation_units,6)
        payload={"steps":steps,"tokens":tokens,"verification_depth":verification_depth,"speculation_width":speculation_width,"retry_attempts":retry_attempts,"aggregation_units":aggregation_units,"compute":compute}
        return ReasoningCostEstimate(
            estimate_id=canonical_hash(payload), compute_units=compute, token_units=tokens,
            verification_units=verification_depth*1.5, speculation_units=max(0,speculation_width-1)*2.0,
            retry_units=retry_units, aggregation_units=aggregation_units,
            backend_id=self.backend_id, backend_version=self.backend_version,
            backend_kind=ReasoningBackendKind.DETERMINISTIC,
            operating_domain="structural-budget-units", uncertainty=1.0,
            evidence_ids=tuple(sorted(evidence_ids)))
