from __future__ import annotations

from enum import Enum

from pydantic import Field, field_validator, model_validator

from mercury.contracts.base import ContractModel
from mercury.runtime.recovery_state import FailureCategory, RecoveryAction


class TelemetryEvidenceKind(str, Enum):
    EXECUTION_MEASUREMENT = "execution_measurement"
    FAILURE = "failure"
    RECOVERY = "recovery"


class MeasurementSource(str, Enum):
    MEASURED = "measured"
    SIMULATED = "simulated"
    ESTIMATED = "estimated"
    DERIVED = "derived"


class ExecutionMeasurement(ContractModel):
    metric_name: str
    value: float = Field(allow_inf_nan=False)
    unit: str
    source: MeasurementSource

    @field_validator("metric_name", "unit")
    @classmethod
    def evidence_labels_are_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("measurement evidence labels must be non-empty")
        return value


class TelemetryEvidenceRecord(ContractModel):
    record_id: str
    request_id: str
    workload_id: str
    execution_id: str
    node_id: str
    trace_id: str
    span_id: str
    model_id: str
    hardware_id: str
    precision: str
    context_strategy: str
    measurements: tuple[ExecutionMeasurement, ...] = Field(min_length=1)
    failure_category: FailureCategory | None = None
    recovery_action: RecoveryAction | None = None

    @field_validator(
        "record_id",
        "request_id",
        "workload_id",
        "execution_id",
        "node_id",
        "trace_id",
        "span_id",
        "model_id",
        "hardware_id",
        "precision",
        "context_strategy",
    )
    @classmethod
    def identity_and_configuration_evidence_is_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("telemetry evidence fields must be non-empty")
        return value

    @model_validator(mode="after")
    def metric_names_are_unique(self) -> TelemetryEvidenceRecord:
        names = tuple(measurement.metric_name for measurement in self.measurements)
        if len(names) != len(set(names)):
            raise ValueError("measurement metric names must be unique")
        return self
