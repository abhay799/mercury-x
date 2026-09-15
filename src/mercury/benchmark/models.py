from typing import Literal

from pydantic import Field, model_validator

from mercury.contracts.base import ContractModel
from mercury.contracts.workload_profile import WorkloadProfile
from mercury.contracts.workload_request import WorkloadRequest


BenchmarkCategory = Literal[
    "text_generation_small",
    "text_generation_large",
    "embedding",
    "rag",
    "classification",
    "batch",
    "latency_critical",
    "long_context",
    "agent_tool",
    "multi_model_dag",
]
ExecutionMode = Literal["LOCAL_CPU", "REMOTE_GPU", "SIMULATED"]


class BenchmarkDefinition(ContractModel):
    benchmark_id: str = Field(min_length=1)
    category: BenchmarkCategory
    description: str = Field(min_length=1)
    request: WorkloadRequest
    profile: WorkloadProfile
    allowed_execution_modes: list[ExecutionMode] = Field(min_length=1)
    required_metrics: list[str] = Field(min_length=1)
    evidence_state: Literal["DEFINITION_ONLY"] = "DEFINITION_ONLY"

    @model_validator(mode="after")
    def validate_identity(self):
        if self.request.workload_id != self.profile.workload_id:
            raise ValueError("request/profile workload_id mismatch")
        if "LOCAL_CPU" not in self.allowed_execution_modes:
            raise ValueError("benchmark must remain LOCAL_CPU safe")
        return self


class BenchmarkCatalog(ContractModel):
    definitions: list[BenchmarkDefinition] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unique_ids(self):
        ids = [item.benchmark_id for item in self.definitions]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate benchmark_id")
        return self

    def get(self, benchmark_id: str) -> BenchmarkDefinition:
        for item in self.definitions:
            if item.benchmark_id == benchmark_id:
                return item
        raise KeyError(benchmark_id)
