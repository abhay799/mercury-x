from __future__ import annotations

from typing import Mapping
from uuid import uuid4

from mercury.contracts.slo import SLODefinition, SLOResult


class SLOEvaluator:
    """Compare measured execution evidence with an immutable SLO definition."""

    def evaluate(
        self,
        slo: SLODefinition,
        *,
        workload_id: str,
        execution_id: str,
        measurements: Mapping[str, float],
        observed_privacy_rule: str | None = None,
        slo_result_id: str | None = None,
    ) -> SLOResult:
        evidence = {name: float(value) for name, value in measurements.items()}
        violations: list[str] = []

        self._check_max(
            violations, evidence, "p95_latency_ms", slo.max_p95_latency_ms
        )
        self._check_max(violations, evidence, "ttft_ms", slo.max_ttft_ms)
        self._check_min(violations, evidence, "quality", slo.min_quality)
        self._check_min(violations, evidence, "reliability", slo.min_reliability)
        self._check_max(
            violations, evidence, "cost_per_request", slo.max_cost_per_request
        )

        if slo.privacy_rule is not None:
            if observed_privacy_rule is None:
                violations.append("missing privacy evidence: privacy_rule")
            elif observed_privacy_rule != slo.privacy_rule:
                violations.append(
                    f"privacy_rule must equal {slo.privacy_rule}; observed {observed_privacy_rule}"
                )

        return SLOResult(
            slo_result_id=slo_result_id or f"slo-result-{uuid4().hex}",
            slo_definition_id=slo.slo_id,
            workload_id=workload_id,
            execution_id=execution_id,
            satisfied=not violations,
            measurements=evidence,
            violations=violations,
        )

    @staticmethod
    def _check_max(
        violations: list[str],
        evidence: Mapping[str, float],
        metric: str,
        target: float | None,
    ) -> None:
        if target is None:
            return
        if metric not in evidence:
            violations.append(f"missing measurement: {metric}")
            return
        observed = evidence[metric]
        if observed > target:
            violations.append(f"{metric} must be <= {target}; observed {observed}")

    @staticmethod
    def _check_min(
        violations: list[str],
        evidence: Mapping[str, float],
        metric: str,
        target: float | None,
    ) -> None:
        if target is None:
            return
        if metric not in evidence:
            violations.append(f"missing measurement: {metric}")
            return
        observed = evidence[metric]
        if observed < target:
            violations.append(f"{metric} must be >= {target}; observed {observed}")
