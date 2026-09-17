from typing import Protocol
from mercury.contracts.base import ContractModel
from mercury.reasoning_budget.contracts import BudgetCalibrationState, canonical_hash

class ReasoningCostEstimate(ContractModel):
    estimate_id: str
    compute_units: float
    token_units: int
    verification_units: float
    speculation_units: float
    calibration_state: BudgetCalibrationState = BudgetCalibrationState.UNCALIBRATED

class ReasoningCostBackend(Protocol):
    def estimate(self, *, steps:int, tokens:int, verification_depth:int, speculation_width:int) -> ReasoningCostEstimate: ...

class DeterministicReasoningCostBackend:
    def estimate(self, *, steps, tokens, verification_depth, speculation_width):
        compute=round(steps*1.0 + tokens/1024.0 + verification_depth*1.5 + max(0,speculation_width-1)*2.0,6)
        payload={"steps":steps,"tokens":tokens,"verification_depth":verification_depth,"speculation_width":speculation_width,"compute":compute}
        return ReasoningCostEstimate(
            estimate_id=canonical_hash(payload), compute_units=compute, token_units=tokens,
            verification_units=verification_depth*1.5, speculation_units=max(0,speculation_width-1)*2.0)
