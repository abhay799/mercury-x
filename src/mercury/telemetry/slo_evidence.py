from __future__ import annotations

from enum import Enum

from pydantic import Field, field_validator, model_validator

from mercury.contracts.base import ContractModel
from mercury.telemetry.evidence import MeasurementSource


class SLOComparison(str, Enum):
    LESS_THAN_OR_EQUAL = "less_than_or_equal"
    LESS_THAN = "less_than"
    GREATER_THAN_OR_EQUAL = "greater_than_or_equal"
    GREATER_THAN = "greater_than"
    EQUAL = "equal"


class SLOMetricEvaluation(ContractModel):
    metric_name: str
    observed_value: float = Field(allow_inf_nan=False)
    target_value: float = Field(allow_inf_nan=False)
    unit: str
    comparison: SLOComparison
    passed: bool
    source: MeasurementSource
    violation_reason: str | None = None

    @field_validator("metric_name", "unit", "violation_reason")
    @classmethod
    def text_evidence_is_non_empty_when_present(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("SLO evidence text must be non-empty")
        return value

    @model_validator(mode="after")
    def result_and_violation_evidence_are_consistent(self) -> SLOMetricEvaluation:
        comparisons = {
            SLOComparison.LESS_THAN_OR_EQUAL: self.observed_value <= self.target_value,
            SLOComparison.LESS_THAN: self.observed_value < self.target_value,
            SLOComparison.GREATER_THAN_OR_EQUAL: self.observed_value >= self.target_value,
            SLOComparison.GREATER_THAN: self.observed_value > self.target_value,
            SLOComparison.EQUAL: self.observed_value == self.target_value,
        }
        if self.passed is not comparisons[self.comparison]:
            raise ValueError("passed result does not match the metric comparison")
        if not self.passed and not self.violation_reason:
            raise ValueError("failed metric requires an explicit violation reason")
        if self.passed and self.violation_reason:
            raise ValueError("passed metric cannot carry a violation reason")
        return self


class SLOEvaluationEvidence(ContractModel):
    evaluation_id: str
    workload_id: str
    execution_id: str
    slo_version: str
    overall_passed: bool
    metric_evaluations: tuple[SLOMetricEvaluation, ...] = Field(min_length=1)

    @field_validator("evaluation_id", "workload_id", "execution_id", "slo_version")
    @classmethod
    def identity_evidence_is_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("SLO evidence identity must be non-empty")
        return value

    @model_validator(mode="after")
    def aggregate_result_and_metric_names_are_consistent(self) -> SLOEvaluationEvidence:
        names = tuple(metric.metric_name for metric in self.metric_evaluations)
        if len(names) != len(set(names)):
            raise ValueError("metric names must be unique")
        if self.overall_passed is not all(metric.passed for metric in self.metric_evaluations):
            raise ValueError("overall result must match contained metric results")
        return self
