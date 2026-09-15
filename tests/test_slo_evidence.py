from __future__ import annotations

import math

import pytest
from pydantic import ValidationError

from mercury.telemetry.evidence import MeasurementSource
from mercury.telemetry.slo_evidence import (
    SLOComparison,
    SLOEvaluationEvidence,
    SLOMetricEvaluation,
)


def metric(**overrides: object) -> SLOMetricEvaluation:
    values: dict[str, object] = {
        "metric_name": "latency_ms",
        "observed_value": 25.0,
        "target_value": 30.0,
        "unit": "ms",
        "comparison": SLOComparison.LESS_THAN_OR_EQUAL,
        "passed": True,
        "source": MeasurementSource.MEASURED,
        "violation_reason": None,
    }
    values.update(overrides)
    return SLOMetricEvaluation(**values)


def evidence(**overrides: object) -> SLOEvaluationEvidence:
    values: dict[str, object] = {
        "evaluation_id": "evaluation-1",
        "workload_id": "workload-1",
        "execution_id": "execution-1",
        "slo_version": "mercury.slo/v1",
        "overall_passed": True,
        "metric_evaluations": (metric(),),
    }
    values.update(overrides)
    return SLOEvaluationEvidence(**values)


def test_valid_passing_slo_evidence():
    assert evidence().overall_passed is True


def test_valid_failing_slo_evidence():
    failed = metric(
        observed_value=35.0,
        passed=False,
        violation_reason="latency target exceeded",
    )
    assert evidence(overall_passed=False, metric_evaluations=(failed,)).overall_passed is False


@pytest.mark.parametrize("field", ["evaluation_id", "workload_id", "execution_id", "slo_version"])
def test_blank_evidence_ids_are_rejected(field: str):
    with pytest.raises(ValidationError):
        evidence(**{field: " "})


@pytest.mark.parametrize("field", ["metric_name", "unit"])
def test_blank_metric_name_or_unit_is_rejected(field: str):
    with pytest.raises(ValidationError):
        metric(**{field: " "})


@pytest.mark.parametrize("field", ["observed_value", "target_value"])
@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_non_finite_metric_values_are_rejected(field: str, value: float):
    with pytest.raises(ValidationError):
        metric(**{field: value})


def test_failed_metric_requires_explicit_violation_reason():
    with pytest.raises(ValidationError):
        metric(observed_value=35.0, passed=False)


def test_passed_metric_cannot_carry_violation_reason():
    with pytest.raises(ValidationError):
        metric(violation_reason="unexpected")


def test_duplicate_metric_names_are_rejected():
    item = metric()
    with pytest.raises(ValidationError):
        evidence(metric_evaluations=(item, item))


def test_overall_passed_must_match_metric_results():
    failed = metric(
        observed_value=35.0,
        passed=False,
        violation_reason="latency target exceeded",
    )
    with pytest.raises(ValidationError):
        evidence(overall_passed=True, metric_evaluations=(failed,))


def test_measured_and_simulated_sources_remain_explicit():
    measured = metric(source=MeasurementSource.MEASURED)
    simulated = metric(source=MeasurementSource.SIMULATED)
    assert measured.source is MeasurementSource.MEASURED
    assert simulated.source is MeasurementSource.SIMULATED


def test_metric_collections_are_immutable():
    evaluation = evidence()
    assert isinstance(evaluation.metric_evaluations, tuple)
    with pytest.raises((AttributeError, TypeError, ValidationError)):
        evaluation.metric_evaluations += (metric(metric_name="throughput"),)


@pytest.mark.parametrize("field", ["payload", "api_key", "token", "credentials"])
def test_raw_payload_and_secret_extra_fields_are_rejected(field: str):
    with pytest.raises(ValidationError):
        evidence(**{field: "forbidden"})


def test_workload_execution_and_slo_version_identity_is_preserved():
    evaluation = evidence()
    assert evaluation.workload_id == "workload-1"
    assert evaluation.execution_id == "execution-1"
    assert evaluation.slo_version == "mercury.slo/v1"
