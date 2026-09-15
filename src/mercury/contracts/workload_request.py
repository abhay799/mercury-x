from typing import Any, Literal
from pydantic import Field
from .base import ContractModel


class WorkloadRequest(ContractModel):
    schema_version: Literal["mercury.workload.request/v1"] = "mercury.workload.request/v1"
    workload_id: str = Field(min_length=1)
    session_id: str | None = None
    task_type: str = Field(min_length=1)
    input: dict[str, Any]
    context: dict[str, Any] = Field(default_factory=dict)
    latency_target_ms: float = Field(gt=0)
    quality_target: float = Field(ge=0, le=1)
    cost_budget: float | None = Field(default=None, ge=0)
    privacy_level: str = Field(min_length=1)
    priority: int = Field(default=50, ge=0, le=100)
    hardware_constraints: list[str] = Field(default_factory=list)
