from __future__ import annotations

import pytest
from pydantic import ValidationError

from mercury.runtime.failure_scenarios import (
    ExpectedRecoveryOutcome,
    FailureInjectionScenario,
    FailureScenarioExpectation,
    FailureScenarioKind,
)


def scenario(**overrides: object) -> FailureInjectionScenario:
    values: dict[str, object] = {
        "scenario_id": "scenario-1",
        "scenario_kind": FailureScenarioKind.WORKER_CRASH,
        "target_execution_id": "execution-1",
        "target_node_id": "node-1",
        "trigger_attempt": 0,
        "description": "worker exits during node execution",
        "expected_recovery": ExpectedRecoveryOutcome.RESCHEDULE,
    }
    values.update(overrides)
    return FailureInjectionScenario(**values)


def expectation(**overrides: object) -> FailureScenarioExpectation:
    values: dict[str, object] = {
        "expectation_id": "expectation-1",
        "scenarios": (scenario(),),
        "hard_constraints_preserved": True,
        "budget_constraints_preserved": True,
    }
    values.update(overrides)
    return FailureScenarioExpectation(**values)


def test_valid_failure_scenario():
    assert scenario().scenario_kind is FailureScenarioKind.WORKER_CRASH


@pytest.mark.parametrize(
    "field", ["scenario_id", "target_execution_id", "target_node_id"]
)
def test_blank_scenario_execution_or_node_ids_are_rejected(field: str):
    with pytest.raises(ValidationError):
        scenario(**{field: " "})


def test_negative_trigger_attempt_is_rejected():
    with pytest.raises(ValidationError):
        scenario(trigger_attempt=-1)


def test_empty_description_is_rejected():
    with pytest.raises(ValidationError):
        scenario(description=" ")


def test_missing_expected_recovery_is_rejected():
    values = scenario().model_dump()
    del values["expected_recovery"]
    with pytest.raises(ValidationError):
        FailureInjectionScenario(**values)


def test_explicit_recovery_outcome_is_preserved():
    item = scenario(expected_recovery=ExpectedRecoveryOutcome.MIGRATE)
    assert item.expected_recovery is ExpectedRecoveryOutcome.MIGRATE


def test_duplicate_scenario_ids_are_rejected_in_expectation_set():
    item = scenario()
    with pytest.raises(ValidationError):
        expectation(scenarios=(item, item))


def test_impossible_slo_scenario_cannot_relax_hard_constraints():
    item = scenario(scenario_kind=FailureScenarioKind.IMPOSSIBLE_SLO)
    with pytest.raises(ValidationError):
        expectation(scenarios=(item,), hard_constraints_preserved=False)


def test_budget_exceeded_scenario_cannot_ignore_budget_hard_constraints():
    item = scenario(scenario_kind=FailureScenarioKind.BUDGET_EXCEEDED)
    with pytest.raises(ValidationError):
        expectation(scenarios=(item,), budget_constraints_preserved=False)


def test_scenario_and_expectation_containers_are_immutable():
    bundle = expectation()
    assert isinstance(bundle.scenarios, tuple)
    with pytest.raises((AttributeError, TypeError, ValidationError)):
        bundle.scenarios += (scenario(scenario_id="scenario-2"),)


@pytest.mark.parametrize("field", ["payload", "api_key", "token", "credentials"])
def test_payload_and_secret_extra_fields_are_rejected(field: str):
    with pytest.raises(ValidationError):
        scenario(**{field: "forbidden"})


def test_failure_kind_identity_is_preserved():
    item = scenario(scenario_kind=FailureScenarioKind.OUT_OF_MEMORY)
    assert item.scenario_kind is FailureScenarioKind.OUT_OF_MEMORY


def test_execution_and_node_identity_is_preserved():
    item = scenario()
    assert item.target_execution_id == "execution-1"
    assert item.target_node_id == "node-1"
