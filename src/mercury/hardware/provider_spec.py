from typing import Literal
from pydantic import Field, model_validator
from mercury.contracts.base import ContractModel

ProviderKind = Literal[
    "LOCAL_CPU",
    "LOCAL_GPU",
    "KAGGLE_GPU",
    "COLAB_GPU",
    "FRIEND_GPU",
    "CLOUD_GPU",
]
TrustLevel = Literal["LOCAL_TRUSTED", "ORGANIZATION_TRUSTED", "APPROVED_REMOTE", "EXTERNAL_CLOUD"]
EvidenceSupport = Literal["MEASURED", "SIMULATED", "BOTH"]

class HardwareProviderSpec(ContractModel):
    provider_id: str = Field(min_length=1)
    provider_kind: ProviderKind
    trust_level: TrustLevel
    enabled: bool = True
    supports_gpu: bool
    supports_cpu: bool
    supports_remote_execution: bool
    supports_persistent_workers: bool = False
    evidence_support: EvidenceSupport
    cost_class: Literal["FREE", "LOW", "PAID", "VARIABLE"]
    secret_names: list[str] = Field(default_factory=list)
    notes: str = ""

    @model_validator(mode="after")
    def validate_shape(self):
        if self.provider_kind == "LOCAL_CPU" and self.supports_remote_execution:
            raise ValueError("LOCAL_CPU cannot be remote")
        if self.provider_kind in {"KAGGLE_GPU", "COLAB_GPU", "FRIEND_GPU", "CLOUD_GPU"} and not self.supports_remote_execution:
            raise ValueError("remote GPU providers must support remote execution")
        if self.provider_kind.endswith("_GPU") and not self.supports_gpu:
            raise ValueError("GPU provider must support GPU")
        return self

class HardwareProviderCatalog(ContractModel):
    providers: list[HardwareProviderSpec] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unique_ids(self):
        ids = [p.provider_id for p in self.providers]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate provider_id")
        if not any(p.provider_kind == "LOCAL_CPU" and p.enabled for p in self.providers):
            raise ValueError("an enabled LOCAL_CPU provider is required")
        return self

    def get(self, provider_id: str) -> HardwareProviderSpec:
        for provider in self.providers:
            if provider.provider_id == provider_id:
                return provider
        raise KeyError(provider_id)
