from typing import Literal
from pydantic import Field, model_validator
from .base import ContractModel

CapabilityLabel = Literal["PRODUCTION", "EXPERIMENTAL", "SIMULATED", "RESEARCH", "PLANNED"]
EvidenceType = Literal["MEASURED", "SIMULATED"]


class HardwareProfile(ContractModel):
    schema_version: Literal["mercury.hardware.profile/v1"] = "mercury.hardware.profile/v1"
    hardware_id: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    hardware_type: str = Field(min_length=1)
    vendor: str | None = None
    architecture: str | None = None
    memory_gb: float = Field(gt=0)
    available_memory_gb: float = Field(ge=0)
    supported_precisions: list[str] = Field(default_factory=list)
    topology_tags: list[str] = Field(default_factory=list)
    runtime_tags: list[str] = Field(default_factory=list)
    capability_labels: list[CapabilityLabel] = Field(default_factory=list)
    evidence_type: EvidenceType

    @model_validator(mode="after")
    def validate_available_memory(self):
        if self.available_memory_gb > self.memory_gb:
            raise ValueError("available_memory_gb cannot exceed memory_gb")
        return self
