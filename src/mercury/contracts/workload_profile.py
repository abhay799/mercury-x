from typing import Literal
from pydantic import Field
from .base import ContractModel


class WorkloadProfile(ContractModel):
    schema_version: Literal["mercury.workload.profile/v1"] = "mercury.workload.profile/v1"
    workload_id: str = Field(min_length=1)
    required_modalities: list[str] = Field(default_factory=list)
    reasoning_complexity: Literal["low", "medium", "high", "extreme"] = "medium"
    required_capabilities: list[str] = Field(default_factory=list)
    context_bytes: int = Field(default=0, ge=0)
    latency_sensitive: bool = False
    quality_target: float = Field(ge=0, le=1)
    privacy_level: str = Field(min_length=1)
    required_tools: list[str] = Field(default_factory=list)
