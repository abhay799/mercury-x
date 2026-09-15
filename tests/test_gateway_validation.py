from __future__ import annotations

import pytest
from pydantic import ValidationError

from mercury.contracts.workload_request import WorkloadRequest
from mercury.gateway.identity import GatewayIdentity
from mercury.gateway.validation import (
    GatewayValidationCode,
    GatewayValidationIssue,
    GatewayValidationResult,
    validate_gateway_request,
)


def request_data(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "workload_id": "workload-1",
        "session_id": "session-1",
        "task_type": "inference",
        "input": {"prompt_reference": "mercury://input/1"},
        "context": {"context_reference": "mercury://context/1"},
        "latency_target_ms": 100.0,
        "quality_target": 0.9,
        "cost_budget": 1.0,
        "privacy_level": "confidential",
        "priority": 50,
        "hardware_constraints": ["cpu"],
    }
    values.update(overrides)
    return values


def identity_data(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "request_id": "request-1",
        "workload_id": "workload-1",
        "session_id": "session-1",
    }
    values.update(overrides)
    return values


def test_valid_request_is_accepted():
    result = validate_gateway_request(identity_data(), WorkloadRequest(**request_data()))
    assert result.accepted is True
    assert isinstance(result.validated_request, WorkloadRequest)


@pytest.mark.parametrize("field", ["request_id", "workload_id", "session_id"])
def test_invalid_required_identity_is_rejected(field: str):
    result = validate_gateway_request(identity_data(**{field: " "}), request_data())
    assert result.accepted is False
    assert any(issue.field_name == field for issue in result.issues)


def test_malformed_request_is_rejected():
    result = validate_gateway_request(identity_data(), request_data(latency_target_ms=0))
    assert result.accepted is False
    assert result.validated_request is None


def test_rejected_result_contains_explicit_error_issue():
    result = validate_gateway_request(identity_data(), request_data(task_type=""))
    assert result.issues
    assert all(issue.message.strip() for issue in result.issues)
    assert any(issue.severity == "error" for issue in result.issues)


def test_accepted_result_has_no_error_issues():
    result = validate_gateway_request(identity_data(), request_data())
    assert result.accepted is True
    assert not any(issue.severity == "error" for issue in result.issues)


def test_original_workload_request_remains_unchanged():
    original = WorkloadRequest(**request_data())
    before = original.model_dump(mode="python")
    result = validate_gateway_request(identity_data(), original)
    assert result.validated_request is original
    assert original.model_dump(mode="python") == before


def test_request_workload_and_session_identity_is_preserved():
    result = validate_gateway_request(identity_data(), request_data())
    assert (result.request_id, result.workload_id, result.session_id) == (
        "request-1",
        "workload-1",
        "session-1",
    )


def test_forbidden_unknown_field_is_rejected():
    result = validate_gateway_request(
        identity_data(), request_data(unknown_required_constraint="forbidden")
    )
    assert result.accepted is False
    assert any(issue.code is GatewayValidationCode.FORBIDDEN_FIELD for issue in result.issues)


def test_validation_result_is_immutable():
    result = validate_gateway_request(identity_data(), request_data())
    with pytest.raises((AttributeError, TypeError, ValidationError)):
        result.accepted = False


def test_issue_collection_is_immutable():
    result = validate_gateway_request(identity_data(), request_data())
    assert isinstance(result.issues, tuple)
    with pytest.raises((AttributeError, TypeError, ValidationError)):
        result.issues += (
            GatewayValidationIssue(
                code=GatewayValidationCode.MALFORMED_REQUEST,
                field_name="task_type",
                message="invalid task type",
                severity="error",
            ),
        )


def test_no_model_selection_fields_are_exposed():
    fields = set(GatewayValidationResult.model_fields)
    assert "selected_model_id" not in fields
    assert "model_selection" not in fields


def test_no_hardware_selection_fields_are_exposed():
    fields = set(GatewayValidationResult.model_fields)
    assert "selected_hardware_id" not in fields
    assert "hardware_selection" not in fields


def test_no_workload_intelligence_properties_are_inferred():
    fields = set(GatewayValidationResult.model_fields)
    assert not fields.intersection(
        {"complexity", "modality", "estimated_tokens", "workload_features"}
    )
