from __future__ import annotations

import math

import pytest
from pydantic import ValidationError

from mercury.runtime.recovery_state import FailureCategory, RecoveryAction
from mercury.telemetry.evidence import (
    ExecutionMeasurement,
    MeasurementSource,
    TelemetryEvidenceRecord,
)


def measurement(**overrides: object) -> ExecutionMeasurement:
    values: dict[str, object] = {
        "metric_name": "latency_ms",
        "value": 25.0,
        "unit": "ms",
        "source": MeasurementSource.MEASURED,
    }
    values.update(overrides)
    return ExecutionMeasurement(**values)


def record(**overrides: object) -> TelemetryEvidenceRecord:
    values: dict[str, object] = {
        "record_id": "record-1",
        "request_id": "request-1",
        "workload_id": "workload-1",
        "execution_id": "execution-1",
        "node_id": "node-1",
        "trace_id": "trace-1",
        "span_id": "span-1",
        "model_id": "model-1",
        "hardware_id": "hardware-1",
        "precision": "fp16",
        "context_strategy": "isolated",
        "measurements": (measurement(),),
        "failure_category": None,
        "recovery_action": None,
    }
    values.update(overrides)
    return TelemetryEvidenceRecord(**values)


def test_valid_telemetry_evidence_record():
    assert record().record_id == "record-1"


@pytest.mark.parametrize(
    "field", ["record_id", "request_id", "workload_id", "execution_id", "node_id"]
)
def test_blank_core_identity_ids_are_rejected(field: str):
    with pytest.raises(ValidationError):
        record(**{field: " "})


def test_blank_metric_name_is_rejected():
    with pytest.raises(ValidationError):
        measurement(metric_name=" ")


def test_blank_unit_is_rejected():
    with pytest.raises(ValidationError):
        measurement(unit=" ")


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_non_finite_measurement_values_are_rejected(value: float):
    with pytest.raises(ValidationError):
        measurement(value=value)


def test_duplicate_metric_names_are_rejected():
    item = measurement()
    with pytest.raises(ValidationError):
        record(measurements=(item, item))


def test_measured_and_simulated_evidence_remain_distinguishable():
    measured = measurement(source=MeasurementSource.MEASURED)
    simulated = measurement(source=MeasurementSource.SIMULATED)
    assert measured.source is MeasurementSource.MEASURED
    assert simulated.source is MeasurementSource.SIMULATED


def test_telemetry_collections_are_immutable():
    evidence = record()
    assert isinstance(evidence.measurements, tuple)
    with pytest.raises((AttributeError, TypeError, ValidationError)):
        evidence.measurements += (measurement(metric_name="tokens"),)


@pytest.mark.parametrize("field", ["payload", "api_key", "token", "credentials"])
def test_raw_payload_and_secret_fields_are_rejected(field: str):
    with pytest.raises(ValidationError):
        record(**{field: "forbidden"})


def test_trace_model_and_hardware_identity_is_preserved():
    evidence = record()
    assert evidence.trace_id == "trace-1"
    assert evidence.model_id == "model-1"
    assert evidence.hardware_id == "hardware-1"


def test_optional_failure_evidence_is_preserved():
    evidence = record(failure_category=FailureCategory.RUNTIME_FAILURE)
    assert evidence.failure_category is FailureCategory.RUNTIME_FAILURE


def test_optional_recovery_action_evidence_is_preserved():
    evidence = record(recovery_action=RecoveryAction.MIGRATE)
    assert evidence.recovery_action is RecoveryAction.MIGRATE


def test_simulated_evidence_cannot_be_relabelled_as_measured_after_validation():
    simulated = measurement(source=MeasurementSource.SIMULATED)
    with pytest.raises((AttributeError, TypeError, ValidationError)):
        simulated.source = MeasurementSource.MEASURED
