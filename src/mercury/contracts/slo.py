from typing import Literal
from pydantic import Field
from .base import ContractModel


class SLODefinition(ContractModel):
    schema_version: Literal["mercury.slo.definition/v1"] = "mercury.slo.definition/v1"
    slo_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    max_p95_latency_ms: float | None = Field(default=None, gt=0)
    max_ttft_ms: float | None = Field(default=None, gt=0)
    min_quality: float | None = Field(default=None, ge=0, le=1)
    min_reliability: float | None = Field(default=None, ge=0, le=1)
    max_cost_per_request: float | None = Field(default=None, ge=0)
    privacy_rule: str | None = None


class SLOResult(ContractModel):
    schema_version: Literal["mercury.slo.result/v1"] = "mercury.slo.result/v1"
    slo_result_id: str = Field(min_length=1)
    slo_definition_id: str = Field(min_length=1)
    workload_id: str = Field(min_length=1)
    execution_id: str = Field(min_length=1)
    satisfied: bool
    measurements: dict[str, float] = Field(default_factory=dict)
    violations: list[str] = Field(default_factory=list)
