from __future__ import annotations

from dataclasses import dataclass
from numbers import Real
from typing import Any, Mapping

from mercury.contracts.policy import PolicySet


class PolicyConfigurationError(ValueError):
    """Raised when a policy rule cannot be evaluated safely."""


@dataclass(frozen=True)
class PolicyEvaluation:
    allowed: bool
    satisfied_constraints: tuple[str, ...]
    violations: tuple[str, ...]
    objective_observations: dict[str, float]
    missing_objectives: tuple[str, ...]


class PolicyEvaluator:
    """Evaluate hard constraints and expose objective evidence without ranking."""

    _SUPPORTED_OPERATORS = {"eq", "neq", "lte", "gte", "in", "contains"}

    def evaluate(self, policy: PolicySet, facts: Mapping[str, Any]) -> PolicyEvaluation:
        satisfied: list[str] = []
        violations: list[str] = []

        for name, rule in policy.hard_constraints.items():
            if name not in facts:
                violations.append(f"missing required fact: {name}")
                continue

            operator, expected = self._parse_rule(name, rule)
            observed = facts[name]
            passed, reason = self._evaluate_rule(name, operator, expected, observed)
            if passed:
                satisfied.append(name)
            else:
                violations.append(reason)

        observations: dict[str, float] = {}
        missing_objectives: list[str] = []
        for objective in policy.optimization_objectives:
            observed = facts.get(objective.name)
            if isinstance(observed, Real) and not isinstance(observed, bool):
                observations[objective.name] = float(observed)
            else:
                missing_objectives.append(objective.name)

        return PolicyEvaluation(
            allowed=not violations,
            satisfied_constraints=tuple(satisfied),
            violations=tuple(violations),
            objective_observations=observations,
            missing_objectives=tuple(missing_objectives),
        )

    def _parse_rule(self, name: str, rule: Any) -> tuple[str, Any]:
        if not isinstance(rule, dict):
            return "eq", rule

        if set(rule) != {"operator", "value"}:
            raise PolicyConfigurationError(
                f"hard constraint {name!r} must contain exactly 'operator' and 'value'"
            )
        operator = rule["operator"]
        if operator not in self._SUPPORTED_OPERATORS:
            raise PolicyConfigurationError(f"unsupported operator {operator!r} for {name}")
        return operator, rule["value"]

    def _evaluate_rule(
        self, name: str, operator: str, expected: Any, observed: Any
    ) -> tuple[bool, str]:
        if operator == "eq":
            passed = observed == expected
            return passed, f"{name} must equal {expected}; observed {observed}"

        if operator == "neq":
            passed = observed != expected
            return passed, f"{name} must not equal {expected}; observed {observed}"

        if operator in {"lte", "gte"}:
            self._require_numeric(name, expected, observed)
            if operator == "lte":
                passed = observed <= expected
                return passed, f"{name} must be <= {expected}; observed {observed}"
            passed = observed >= expected
            return passed, f"{name} must be >= {expected}; observed {observed}"

        if operator == "in":
            try:
                passed = observed in expected
            except TypeError as exc:
                raise PolicyConfigurationError(
                    f"hard constraint {name!r} with 'in' requires a container value"
                ) from exc
            return passed, f"{name} must be in {expected}; observed {observed}"

        if operator == "contains":
            try:
                passed = expected in observed
            except TypeError as exc:
                raise PolicyConfigurationError(
                    f"hard constraint {name!r} with 'contains' requires a container fact"
                ) from exc
            return passed, f"{name} must contain {expected}; observed {observed}"

        raise PolicyConfigurationError(f"unsupported operator {operator!r} for {name}")

    @staticmethod
    def _require_numeric(name: str, expected: Any, observed: Any) -> None:
        valid_expected = isinstance(expected, Real) and not isinstance(expected, bool)
        valid_observed = isinstance(observed, Real) and not isinstance(observed, bool)
        if not (valid_expected and valid_observed):
            raise PolicyConfigurationError(
                f"hard constraint {name!r} requires numeric values for range comparison"
            )
