from typing import Literal
from pydantic import Field
from .base import ContractModel

CapabilityLabel = Literal["PRODUCTION", "EXPERIMENTAL", "SIMULATED", "RESEARCH", "PLANNED"]


class ModelProfile(ContractModel):
    schema_version: Literal["mercury.model.profile/v1"] = "mercury.model.profile/v1"
    model_id: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    family: str = Field(min_length=1)
    version: str = Field(min_length=1)
    capabilities: list[str] = Field(default_factory=list)
    supported_precisions: list[str] = Field(default_factory=list)
    context_window_tokens: int = Field(gt=0)
    min_memory_gb: float = Field(ge=0)
    estimated_cost_per_1k_tokens: float | None = Field(default=None, ge=0)
    capability_labels: list[CapabilityLabel] = Field(default_factory=list)
