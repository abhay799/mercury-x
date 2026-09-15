from datetime import datetime, timezone
from typing import Literal
from pydantic import Field
from .base import ContractModel


class ExecutionPlan(ContractModel):
    schema_version: Literal["mercury.execution.plan/v1"] = "mercury.execution.plan/v1"
    plan_id: str = Field(min_length=1)
    workload_id: str = Field(min_length=1)
    graph_id: str = Field(min_length=1)
    model_assignments: dict[str, str] = Field(default_factory=dict)
    precision_assignments: dict[str, str] = Field(default_factory=dict)
    hardware_assignments: dict[str, str] = Field(default_factory=dict)
    context_placements: dict[str, str] = Field(default_factory=dict)
    predicted_metrics: dict[str, float] = Field(default_factory=dict)
    policy_version: str = Field(min_length=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
