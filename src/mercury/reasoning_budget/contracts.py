import hashlib, json
from enum import Enum
from pydantic import Field, field_validator, model_validator
from mercury.contracts.base import ContractModel


def canonical_hash(payload) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


class WorkloadDifficulty(str, Enum):
    LOW="LOW"; MEDIUM="MEDIUM"; HIGH="HIGH"; EXTREME="EXTREME"; UNKNOWN="UNKNOWN"


class ReasoningBudgetDecisionState(str, Enum):
    ACCEPTED="ACCEPTED"; ESCALATION_REQUIRED="ESCALATION_REQUIRED"; UNSATISFIABLE="UNSATISFIABLE"; UNKNOWN="UNKNOWN"


class BudgetCalibrationState(str, Enum):
    UNCALIBRATED="UNCALIBRATED"; EMPIRICALLY_CALIBRATED="EMPIRICALLY_CALIBRATED"


class ReasoningBudgetRequest(ContractModel):
    request_id: str
    workload_id: str
    segment_id: str
    requirement_interface_id: str
    quality_metric_id: str
    quality_floor: float = Field(ge=0.0, le=1.0)
    confidence_floor: float = Field(ge=0.0, le=1.0)
    max_reasoning_steps: int = Field(ge=1)
    max_tokens: int = Field(ge=1)
    max_compute_units: float = Field(gt=0)
    max_speculative_branches: int = Field(ge=1)
    verification_depth_min: int = Field(ge=0)
    latency_ceiling_ms: int = Field(ge=1)
    escalation_policy_id: str
    stop_policy_id: str
    provenance_ids: tuple[str, ...] = ()

    @field_validator("request_id", "workload_id", "segment_id", "requirement_interface_id", "quality_metric_id", "escalation_policy_id", "stop_policy_id")
    @classmethod
    def required_identity(cls, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("reasoning budget identity must be nonblank")
        return value

    @field_validator("provenance_ids")
    @classmethod
    def unique_provenance(cls, v):
        if not v or any(not item.strip() for item in v) or len(v) != len(set(v)):
            raise ValueError("duplicate provenance_ids")
        return tuple(sorted(v))


class ReasoningBudgetCandidate(ContractModel):
    candidate_id: str
    reasoning_steps: int = Field(ge=1)
    max_tokens: int = Field(ge=1)
    compute_units: float = Field(gt=0)
    verification_depth: int = Field(ge=0)
    speculation_width: int = Field(ge=1)
    expected_quality_low: float | None = Field(default=None, ge=0, le=1)
    expected_quality_high: float | None = Field(default=None, ge=0, le=1)
    expected_latency_ms: int | None = Field(default=None, ge=1)
    uncertainty: float = Field(ge=0, le=1)
    calibration_state: BudgetCalibrationState = BudgetCalibrationState.UNCALIBRATED
    evidence_ids: tuple[str, ...] = ()

    @model_validator(mode="after")
    def quality_range(self):
        if self.expected_quality_low is not None and self.expected_quality_high is not None:
            if self.expected_quality_low > self.expected_quality_high:
                raise ValueError("invalid quality range")
        return self


class BudgetAllocation(ContractModel):
    primary_reasoning_units: float = Field(ge=0)
    verification_units: float = Field(ge=0)
    speculation_units: float = Field(ge=0)
    escalation_units: float = Field(ge=0)
    aggregation_units: float = Field(ge=0)

    @property
    def total(self):
        return (
            self.primary_reasoning_units + self.verification_units + self.speculation_units
            + self.escalation_units + self.aggregation_units
        )


class ReasoningBudget(ContractModel):
    reasoning_budget_id: str
    request_id: str
    segment_id: str
    chosen_candidate_id: str
    allocation: BudgetAllocation
    quality_floor: float
    confidence_floor: float
    verification_depth: int
    escalation_conditions: tuple[str, ...]
    stop_conditions: tuple[str, ...]
    calibration_state: BudgetCalibrationState
    generation: int = Field(ge=1)
    evidence_ids: tuple[str, ...] = ()
    fingerprint: str

    @model_validator(mode="after")
    def validate_budget_integrity(self):
        body={"id":self.reasoning_budget_id,"request":self.request_id,"candidate":self.chosen_candidate_id,
              "generation":self.generation,"allocation":self.allocation.model_dump(mode="json"),
              "quality_floor":self.quality_floor,"confidence_floor":self.confidence_floor,
              "verification_depth":self.verification_depth}
        if self.reasoning_budget_id != make_budget_id(self.request_id, self.chosen_candidate_id, self.generation):
            raise ValueError("reasoning budget identity mismatch")
        if self.fingerprint != canonical_hash(body):
            raise ValueError("reasoning budget fingerprint mismatch")
        return self


class ReasoningBudgetDecision(ContractModel):
    decision_id: str
    state: ReasoningBudgetDecisionState
    reasoning_budget_id: str | None = None
    reason_codes: tuple[str, ...] = ()


def make_candidate_id(payload) -> str:
    return canonical_hash({"reasoning_budget_candidate": payload})


def make_budget_id(request_id: str, candidate_id: str, generation: int) -> str:
    return canonical_hash({"request_id": request_id, "candidate_id": candidate_id, "generation": generation})
