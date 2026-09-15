from __future__ import annotations

import pytest
from pydantic import ValidationError

from mercury.contracts.workload_request import WorkloadRequest
from mercury.gateway.constraints import (
    CanonicalConstraint,
    ConstraintKind,
    ConstraintNormalizationResult,
    canonicalize_gateway_constraints,
)
from mercury.gateway.identity import GatewayIdentity


def identity() -> GatewayIdentity:
    return GatewayIdentity(
        request_id="request-1",
        workload_id="workload-1",
        session_id="session-1",
    )


def workload(**overrides: object) -> WorkloadRequest:
    values: dict[str, object] = {
        "workload_id": "workload-1",
        "session_id": "session-1",
        "task_type": "inference",
        "input": {"prompt_reference": "mercury://input/1"},
        "context": {},
        "latency_target_ms": 100.0,
        "quality_target": 0.9,
        "cost_budget": 1.0,
        "privacy_level": "confidential",
        "priority": 50,
        "hardware_constraints": [],
    }
    values.update(overrides)
    return WorkloadRequest(**values)


def constraint(**overrides: object) -> CanonicalConstraint:
    values: dict[str, object] = {
        "constraint_id": "custom-1",
        "kind": ConstraintKind.CAPABILITY,
        "operator": "equals",
        "value": "tensor-runtime",
        "unit": None,
        "required": True,
        "source_field": "hardware_constraints",
    }
    values.update(overrides)
    return CanonicalConstraint(**values)


def canonicalize(
    request: WorkloadRequest | None = None,
    additional: tuple[CanonicalConstraint, ...] = (),
) -> ConstraintNormalizationResult:
    return canonicalize_gateway_constraints(
        identity(), request or workload(), additional_constraints=additional
    )


def find(result: ConstraintNormalizationResult, kind: ConstraintKind) -> CanonicalConstraint:
    return next(item for item in result.constraints if item.kind is kind)


def test_valid_latency_constraint_canonicalizes():
    item = find(canonicalize(), ConstraintKind.LATENCY)
    assert (item.operator, item.value, item.unit) == ("less_than_or_equal", 100.0, "ms")


def test_valid_quality_constraint_canonicalizes():
    item = find(canonicalize(), ConstraintKind.QUALITY)
    assert (item.operator, item.value) == ("greater_than_or_equal", 0.9)


def test_valid_cost_constraint_canonicalizes():
    item = find(canonicalize(), ConstraintKind.COST)
    assert (item.operator, item.value) == ("less_than_or_equal", 1.0)


def test_privacy_constraint_remains_explicit():
    item = find(canonicalize(), ConstraintKind.PRIVACY)
    assert item.value == "confidential"
    assert item.required is True


def test_region_constraint_remains_explicit():
    result = canonicalize(workload(hardware_constraints=["region:eu-west-1"]))
    item = find(result, ConstraintKind.REGION)
    assert item.value == "eu-west-1"
    assert item.required is True


def test_equivalent_duplicates_are_deduplicated_deterministically():
    item = constraint()
    result = canonicalize(additional=(item, item.model_copy(update={"constraint_id": "custom-2"})))
    matches = [value for value in result.constraints if value.kind is ConstraintKind.CAPABILITY]
    assert matches == [item]


def test_conflicting_duplicates_produce_error_evidence():
    first = constraint(required=True)
    conflicting = constraint(value="different-runtime")
    result = canonicalize(additional=(first, conflicting))
    assert result.canonicalized is False
    assert result.issues and "conflict" in result.issues[0]


def test_required_constraint_is_not_silently_dropped():
    first = constraint(required=True)
    conflicting = constraint(value="different-runtime")
    result = canonicalize(additional=(first, conflicting))
    assert first in result.constraints


def test_blank_constraint_identity_is_rejected():
    with pytest.raises(ValidationError):
        constraint(constraint_id=" ")


def test_request_workload_and_session_identity_is_preserved():
    result = canonicalize()
    assert (result.request_id, result.workload_id, result.session_id) == (
        "request-1",
        "workload-1",
        "session-1",
    )


def test_constraint_and_issue_collections_are_immutable():
    result = canonicalize()
    assert isinstance(result.constraints, tuple)
    assert isinstance(result.issues, tuple)
    with pytest.raises((AttributeError, TypeError, ValidationError)):
        result.constraints += (constraint(),)


def test_no_model_selection_fields_are_exposed():
    fields = set(ConstraintNormalizationResult.model_fields)
    assert not fields.intersection({"selected_model_id", "model_selection"})


def test_no_hardware_selection_fields_are_exposed():
    fields = set(ConstraintNormalizationResult.model_fields)
    assert not fields.intersection(
        {"selected_hardware_id", "hardware_selection", "placement_id", "scheduler"}
    )


def test_no_reasoning_complexity_is_inferred():
    fields = set(ConstraintNormalizationResult.model_fields)
    assert not fields.intersection({"reasoning_complexity", "complexity", "modality"})
