from __future__ import annotations

from pydantic import field_validator, model_validator

from mercury.contracts.base import ContractModel


class DecisionAlternative(ContractModel):
    alternative_id: str
    model_id: str
    model_configuration_id: str
    precision: str
    hardware_id: str
    context_strategy: str
    selected: bool = False
    rejected: bool = False
    rejection_reason: str | None = None

    @field_validator(
        "alternative_id",
        "model_id",
        "model_configuration_id",
        "precision",
        "hardware_id",
        "context_strategy",
        "rejection_reason",
    )
    @classmethod
    def text_evidence_is_non_empty(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("text evidence must be non-empty")
        return value

    @model_validator(mode="after")
    def rejection_evidence_is_unambiguous(self) -> DecisionAlternative:
        if self.rejected and not self.rejection_reason:
            raise ValueError("rejected alternative requires a rejection reason")
        if self.selected and self.rejected:
            raise ValueError("selected alternative cannot be rejected")
        if not self.rejected and self.rejection_reason:
            raise ValueError("rejection reason requires a rejected alternative")
        return self


class ConstraintEvidence(ContractModel):
    constraint_id: str
    satisfied: bool

    @field_validator("constraint_id")
    @classmethod
    def constraint_id_is_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("constraint id must be non-empty")
        return value


class PredictedMetric(ContractModel):
    metric_name: str
    value: float

    @field_validator("metric_name")
    @classmethod
    def metric_name_is_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("metric name must be non-empty")
        return value


class DecisionProvenance(ContractModel):
    decision_id: str
    workload_id: str
    execution_id: str
    selected_model_id: str
    selected_model_configuration_id: str
    selected_precision: str
    selected_hardware_id: str
    selected_context_strategy: str
    policy_version: str
    slo_version: str
    predicted_metrics: tuple[PredictedMetric, ...]
    constraints_satisfied: tuple[ConstraintEvidence, ...]
    alternatives_considered: tuple[DecisionAlternative, ...]
    rejection_reasons: tuple[str, ...]

    @field_validator(
        "decision_id",
        "workload_id",
        "execution_id",
        "selected_model_id",
        "selected_model_configuration_id",
        "selected_precision",
        "selected_hardware_id",
        "selected_context_strategy",
        "policy_version",
        "slo_version",
    )
    @classmethod
    def required_evidence_is_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("required evidence must be non-empty")
        return value

    @field_validator("rejection_reasons")
    @classmethod
    def rejection_reasons_are_non_empty(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if any(not value.strip() for value in values):
            raise ValueError("rejection reasons must be non-empty")
        return values

    @model_validator(mode="after")
    def evidence_ids_are_unique(self) -> DecisionProvenance:
        alternative_ids = tuple(item.alternative_id for item in self.alternatives_considered)
        if len(alternative_ids) != len(set(alternative_ids)):
            raise ValueError("alternative ids must be unique")
        constraint_ids = tuple(item.constraint_id for item in self.constraints_satisfied)
        if len(constraint_ids) != len(set(constraint_ids)):
            raise ValueError("constraint ids must be unique")
        return self
