from datetime import datetime
from typing import Literal
from pydantic import Field, model_validator
from .base import ContractModel


class TelemetryRecord(ContractModel):
    schema_version: Literal["mercury.telemetry.record/v1"] = "mercury.telemetry.record/v1"
    request_id: str = Field(min_length=1)
    workload_id: str = Field(min_length=1)
    execution_id: str = Field(min_length=1)
    node_id: str | None = None
    model_id: str | None = None
    hardware_id: str | None = None
    scheduler_decision_id: str | None = None
    start_time: datetime
    end_time: datetime
    latency_ms: float = Field(ge=0)
    status: str = Field(min_length=1)
    failure_reason: str | None = None
    resource_usage: dict[str, float] = Field(default_factory=dict)
    slo_result_id: str | None = None

    @model_validator(mode="after")
    def validate_time_order(self):
        if self.end_time < self.start_time:
            raise ValueError("end_time cannot be before start_time")
        return self
