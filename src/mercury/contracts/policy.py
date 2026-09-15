from typing import Any, Literal
from pydantic import Field
from .base import ContractModel


class OptimizationObjective(ContractModel):
    name: str = Field(min_length=1)
    direction: Literal["minimize", "maximize"]
    weight: float = Field(ge=0, le=1)


class PolicySet(ContractModel):
    schema_version: Literal["mercury.policy.set/v1"] = "mercury.policy.set/v1"
    policy_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    hard_constraints: dict[str, Any] = Field(default_factory=dict)
    optimization_objectives: list[OptimizationObjective] = Field(default_factory=list)
    recovery_order: list[str] = Field(
        default_factory=lambda: [
            "RETRY",
            "FALLBACK",
            "RECOMPILE",
            "RESCHEDULE",
            "MIGRATE",
            "DEGRADE",
            "ABSTAIN",
            "FAIL_SAFE",
        ]
    )
