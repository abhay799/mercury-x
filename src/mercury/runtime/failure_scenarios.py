from __future__ import annotations

from enum import Enum

from pydantic import Field, field_validator, model_validator

from mercury.contracts.base import ContractModel


class FailureScenarioKind(str, Enum):
    MODEL_UNAVAILABLE = "model_unavailable"
    WORKER_UNAVAILABLE = "worker_unavailable"
    WORKER_CRASH = "worker_crash"
    TIMEOUT = "timeout"
    OUT_OF_MEMORY = "out_of_memory"
    INVALID_RESPONSE = "invalid_response"
    REGISTRY_UNAVAILABLE = "registry_unavailable"
    NETWORK_FAILURE = "network_failure"
    QUEUE_OVERLOAD = "queue_overload"
    EXECUTION_NODE_FAILURE = "execution_node_failure"
    MISSING_TELEMETRY = "missing_telemetry"
    BUDGET_EXCEEDED = "budget_exceeded"
    IMPOSSIBLE_SLO = "impossible_slo"


class ExpectedRecoveryOutcome(str, Enum):
    RETRY = "retry"
    FALLBACK = "fallback"
    RECOMPILE = "recompile"
    RESCHEDULE = "reschedule"
    MIGRATE = "migrate"
    DEGRADE = "degrade"
    ABSTAIN = "abstain"
    FAIL_SAFE = "fail_safe"


class FailureInjectionScenario(ContractModel):
    scenario_id: str
    scenario_kind: FailureScenarioKind
    target_execution_id: str
    target_node_id: str
    trigger_attempt: int = Field(ge=0)
    description: str
    expected_recovery: ExpectedRecoveryOutcome

    @field_validator(
        "scenario_id", "target_execution_id", "target_node_id", "description"
    )
    @classmethod
    def required_evidence_is_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("failure scenario evidence must be non-empty")
        return value


class FailureScenarioExpectation(ContractModel):
    expectation_id: str
    scenarios: tuple[FailureInjectionScenario, ...] = Field(min_length=1)
    hard_constraints_preserved: bool = True
    budget_constraints_preserved: bool = True

    @field_validator("expectation_id")
    @classmethod
    def expectation_id_is_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("expectation id must be non-empty")
        return value

    @model_validator(mode="after")
    def scenarios_are_unique_and_constraints_are_preserved(
        self,
    ) -> FailureScenarioExpectation:
        scenario_ids = tuple(scenario.scenario_id for scenario in self.scenarios)
        if len(scenario_ids) != len(set(scenario_ids)):
            raise ValueError("scenario ids must be unique")
        scenario_kinds = {scenario.scenario_kind for scenario in self.scenarios}
        if (
            FailureScenarioKind.IMPOSSIBLE_SLO in scenario_kinds
            and not self.hard_constraints_preserved
        ):
            raise ValueError("impossible SLO scenarios cannot relax hard constraints")
        if (
            FailureScenarioKind.BUDGET_EXCEEDED in scenario_kinds
            and not self.budget_constraints_preserved
        ):
            raise ValueError("budget scenarios cannot ignore budget hard constraints")
        return self
