from __future__ import annotations

import pytest
from pydantic import ValidationError

from mercury.runtime.provenance import (
    ConstraintEvidence,
    DecisionAlternative,
    DecisionProvenance,
    PredictedMetric,
)


def alternative(**overrides: object) -> DecisionAlternative:
    values: dict[str, object] = {
        "alternative_id": "alternative-1",
        "model_id": "model-1",
        "model_configuration_id": "config-1",
        "precision": "fp16",
        "hardware_id": "hardware-1",
        "context_strategy": "isolated",
        "selected": True,
        "rejected": False,
    }
    values.update(overrides)
    return DecisionAlternative(**values)


def constraint(**overrides: object) -> ConstraintEvidence:
    values: dict[str, object] = {"constraint_id": "privacy-1", "satisfied": True}
    values.update(overrides)
    return ConstraintEvidence(**values)


def metric(**overrides: object) -> PredictedMetric:
    values: dict[str, object] = {"metric_name": "latency_ms", "value": 25.0}
    values.update(overrides)
    return PredictedMetric(**values)


def make_provenance(**overrides: object) -> DecisionProvenance:
    values: dict[str, object] = {
        "decision_id": "decision-1",
        "workload_id": "workload-1",
        "execution_id": "execution-1",
        "selected_model_id": "model-1",
        "selected_model_configuration_id": "config-1",
        "selected_precision": "fp16",
        "selected_hardware_id": "hardware-1",
        "selected_context_strategy": "isolated",
        "policy_version": "mercury.policy/v1",
        "slo_version": "mercury.slo/v1",
        "predicted_metrics": (metric(),),
        "constraints_satisfied": (constraint(),),
        "alternatives_considered": (alternative(),),
        "rejection_reasons": (),
    }
    values.update(overrides)
    return DecisionProvenance(**values)


def test_valid_provenance_record():
    assert make_provenance().decision_id == "decision-1"


@pytest.mark.parametrize("field", ["decision_id", "workload_id", "execution_id"])
def test_blank_identity_fields_are_rejected(field: str):
    with pytest.raises(ValidationError):
        make_provenance(**{field: " "})


@pytest.mark.parametrize(
    "field", ["selected_model_id", "selected_model_configuration_id", "selected_hardware_id"]
)
def test_blank_selected_model_config_or_hardware_is_rejected(field: str):
    with pytest.raises(ValidationError):
        make_provenance(**{field: " "})


def test_rejected_alternative_requires_explicit_rejection_reason():
    with pytest.raises(ValidationError):
        alternative(selected=False, rejected=True)


def test_duplicate_alternative_ids_are_rejected():
    item = alternative()
    with pytest.raises(ValidationError):
        make_provenance(alternatives_considered=(item, item))


def test_duplicate_constraint_ids_are_rejected():
    item = constraint()
    with pytest.raises(ValidationError):
        make_provenance(constraints_satisfied=(item, item))


def test_selected_alternative_cannot_also_be_rejected():
    with pytest.raises(ValidationError):
        alternative(rejected=True, rejection_reason="policy denied")


def test_predicted_metric_names_must_be_non_empty():
    with pytest.raises(ValidationError):
        metric(metric_name=" ")


def test_provenance_containers_are_immutable():
    provenance = make_provenance()
    assert isinstance(provenance.predicted_metrics, tuple)
    with pytest.raises((AttributeError, TypeError, ValidationError)):
        provenance.rejection_reasons += ("policy denied",)


def test_explicit_policy_slo_model_and_hardware_evidence_is_preserved():
    provenance = make_provenance()
    assert provenance.policy_version == "mercury.policy/v1"
    assert provenance.slo_version == "mercury.slo/v1"
    assert provenance.selected_model_id == "model-1"
    assert provenance.selected_hardware_id == "hardware-1"
