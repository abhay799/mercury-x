from pathlib import Path

import pytest

from mercury.contracts.policy import OptimizationObjective, PolicySet
from mercury.contracts.slo import SLODefinition


def test_hard_constraints_accept_exact_and_numeric_rules():
    from mercury.policy.evaluator import PolicyEvaluator

    policy = PolicySet(
        policy_id="policy-eval-1",
        version="1",
        hard_constraints={
            "privacy": "organization-only",
            "cost_per_request": {"operator": "lte", "value": 0.10},
            "quality": {"operator": "gte", "value": 0.93},
        },
    )
    result = PolicyEvaluator().evaluate(
        policy,
        {"privacy": "organization-only", "cost_per_request": 0.08, "quality": 0.95},
    )

    assert result.allowed is True
    assert result.violations == ()
    assert set(result.satisfied_constraints) == {"privacy", "cost_per_request", "quality"}


def test_hard_constraint_violation_fails_closed_with_reason():
    from mercury.policy.evaluator import PolicyEvaluator

    policy = PolicySet(
        policy_id="policy-eval-2",
        version="1",
        hard_constraints={"cost_per_request": {"operator": "lte", "value": 0.10}},
    )
    result = PolicyEvaluator().evaluate(policy, {"cost_per_request": 0.15})

    assert result.allowed is False
    assert result.violations == ("cost_per_request must be <= 0.1; observed 0.15",)


def test_missing_hard_constraint_fact_fails_closed():
    from mercury.policy.evaluator import PolicyEvaluator

    policy = PolicySet(
        policy_id="policy-eval-3",
        version="1",
        hard_constraints={"privacy": "organization-only"},
    )
    result = PolicyEvaluator().evaluate(policy, {})

    assert result.allowed is False
    assert result.violations == ("missing required fact: privacy",)


def test_unsupported_hard_constraint_operator_is_rejected():
    from mercury.policy.evaluator import PolicyConfigurationError, PolicyEvaluator

    policy = PolicySet(
        policy_id="policy-eval-4",
        version="1",
        hard_constraints={"latency_ms": {"operator": "approximately", "value": 100}},
    )

    with pytest.raises(PolicyConfigurationError, match="unsupported operator"):
        PolicyEvaluator().evaluate(policy, {"latency_ms": 100})


def test_optimization_objectives_are_observed_but_not_ranked():
    from mercury.policy.evaluator import PolicyEvaluator

    policy = PolicySet(
        policy_id="policy-eval-5",
        version="1",
        optimization_objectives=[
            OptimizationObjective(name="latency_ms", direction="minimize", weight=0.6),
            OptimizationObjective(name="quality", direction="maximize", weight=0.4),
        ],
    )
    result = PolicyEvaluator().evaluate(policy, {"latency_ms": 120.0})

    assert result.allowed is True
    assert result.objective_observations == {"latency_ms": 120.0}
    assert result.missing_objectives == ("quality",)
    assert not hasattr(result, "score")


def test_slo_evaluator_marks_complete_evidence_satisfied():
    from mercury.policy.slo_evaluator import SLOEvaluator

    slo = SLODefinition(
        slo_id="slo-eval-1",
        version="1",
        max_p95_latency_ms=2000,
        max_ttft_ms=500,
        min_quality=0.93,
        min_reliability=0.95,
        max_cost_per_request=0.10,
        privacy_rule="organization-only",
    )
    result = SLOEvaluator().evaluate(
        slo,
        workload_id="wl-1",
        execution_id="exec-1",
        measurements={
            "p95_latency_ms": 1500.0,
            "ttft_ms": 300.0,
            "quality": 0.95,
            "reliability": 0.98,
            "cost_per_request": 0.08,
        },
        observed_privacy_rule="organization-only",
        slo_result_id="slo-result-1",
    )

    assert result.satisfied is True
    assert result.violations == []
    assert result.schema_version == "mercury.slo.result/v1"


def test_slo_evaluator_records_threshold_privacy_and_missing_evidence_violations():
    from mercury.policy.slo_evaluator import SLOEvaluator

    slo = SLODefinition(
        slo_id="slo-eval-2",
        version="1",
        max_p95_latency_ms=2000,
        min_quality=0.93,
        min_reliability=0.95,
        privacy_rule="organization-only",
    )
    result = SLOEvaluator().evaluate(
        slo,
        workload_id="wl-2",
        execution_id="exec-2",
        measurements={"p95_latency_ms": 2500.0, "quality": 0.90},
        observed_privacy_rule="external-cloud",
        slo_result_id="slo-result-2",
    )

    assert result.satisfied is False
    assert "p95_latency_ms must be <= 2000.0; observed 2500.0" in result.violations
    assert "quality must be >= 0.93; observed 0.9" in result.violations
    assert "missing measurement: reliability" in result.violations
    assert "privacy_rule must equal organization-only; observed external-cloud" in result.violations


def test_baseline_policy_and_slo_configs_validate_through_contracts():
    from mercury.policy.config_loader import load_policy_set, load_slo_definition

    root = Path(__file__).resolve().parents[1]
    policy = load_policy_set(root / "configs" / "policies" / "default_policy.json")
    slo = load_slo_definition(root / "configs" / "slo" / "default_slo.json")

    assert policy.schema_version == "mercury.policy.set/v1"
    assert policy.hard_constraints["privacy"]["operator"] == "eq"
    assert slo.schema_version == "mercury.slo.definition/v1"
    assert slo.min_quality == 0.93
