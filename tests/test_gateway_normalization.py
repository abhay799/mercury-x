from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from mercury.contracts.workload_request import WorkloadRequest
from mercury.gateway.identity import GatewayIdentity
from mercury.gateway.models import (
    GatewayRequestEnvelope,
    GatewayValidationEvidence,
    GatewayValidationStatus,
)
from mercury.gateway.normalization import (
    NormalizationIssue,
    NormalizationResult,
    normalize_gateway_request,
)


def workload_request(**overrides: object) -> WorkloadRequest:
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
    return WorkloadRequest(**values)


def envelope(request: WorkloadRequest | None = None) -> GatewayRequestEnvelope:
    workload = request or workload_request()
    return GatewayRequestEnvelope(
        gateway_request_id="gateway-request-1",
        identity=GatewayIdentity(
            request_id="request-1",
            workload_id="workload-1",
            session_id="session-1",
        ),
        workload_request=workload,
        received_at=datetime(2026, 9, 16, 12, 0, tzinfo=UTC),
        normalized=False,
        validation_status=GatewayValidationStatus.ACCEPTED,
        validation_evidence=GatewayValidationEvidence(
            status=GatewayValidationStatus.ACCEPTED,
            reasons=(),
        ),
    )


def test_valid_request_normalizes_successfully():
    result = normalize_gateway_request(envelope())
    assert result.normalized is True
    assert result.normalized_request is not None
    assert result.issues == ()


def test_surrounding_whitespace_is_normalized_where_safe():
    request = workload_request(
        task_type="  inference  ",
        privacy_level="  confidential  ",
        hardware_constraints=["  cpu  "],
    )
    normalized = normalize_gateway_request(envelope(request)).normalized_request
    assert normalized is not None
    assert normalized.task_type == "inference"
    assert normalized.privacy_level == "confidential"
    assert normalized.hardware_constraints == ["cpu"]


def test_identity_remains_unchanged():
    gateway_envelope = envelope()
    result = normalize_gateway_request(gateway_envelope)
    assert (result.request_id, result.workload_id, result.session_id) == (
        gateway_envelope.identity.request_id,
        gateway_envelope.identity.workload_id,
        gateway_envelope.identity.session_id,
    )


def test_optional_empty_constraint_strings_canonicalize_safely():
    request = workload_request(hardware_constraints=["cpu", " "])
    normalized = normalize_gateway_request(envelope(request)).normalized_request
    assert normalized is not None
    assert normalized.hardware_constraints == ["cpu"]


def test_duplicate_equivalent_constraint_values_are_deduplicated_deterministically():
    request = workload_request(hardware_constraints=[" cpu ", "gpu", "cpu", " gpu "])
    normalized = normalize_gateway_request(envelope(request)).normalized_request
    assert normalized is not None
    assert normalized.hardware_constraints == ["cpu", "gpu"]


def test_invalid_required_field_produces_explicit_issue():
    result = normalize_gateway_request(envelope(workload_request(task_type=" ")))
    assert result.normalized is False
    assert result.normalized_request is None
    assert result.issues
    assert result.issues[0].field_name == "task_type"
    assert result.issues[0].message.strip()


def test_normalization_does_not_add_model_selection_fields():
    normalized = normalize_gateway_request(envelope()).normalized_request
    assert normalized is not None
    assert "selected_model_id" not in type(normalized).model_fields
    assert "model_selection" not in type(normalized).model_fields


def test_normalization_does_not_add_hardware_selection_fields():
    normalized = normalize_gateway_request(envelope()).normalized_request
    assert normalized is not None
    assert "selected_hardware_id" not in type(normalized).model_fields
    assert "hardware_selection" not in type(normalized).model_fields


def test_semantic_workload_request_values_remain_unchanged():
    original = workload_request()
    before = original.model_dump(mode="python")
    normalized = normalize_gateway_request(envelope(original)).normalized_request
    assert normalized is not None
    assert normalized.input == original.input
    assert normalized.context == original.context
    assert normalized.latency_target_ms == original.latency_target_ms
    assert normalized.quality_target == original.quality_target
    assert normalized.cost_budget == original.cost_budget
    assert original.model_dump(mode="python") == before


def test_unknown_required_constraint_is_not_silently_discarded():
    request = workload_request(hardware_constraints=["future-accelerator-v9"])
    normalized = normalize_gateway_request(envelope(request)).normalized_request
    assert normalized is not None
    assert normalized.hardware_constraints == ["future-accelerator-v9"]


def test_issue_and_result_collections_are_immutable():
    result = normalize_gateway_request(envelope())
    assert isinstance(result.issues, tuple)
    with pytest.raises((AttributeError, TypeError, ValidationError)):
        result.issues += (
            NormalizationIssue(
                field_name="task_type",
                code="invalid",
                message="invalid task type",
                severity="error",
            ),
        )


@pytest.mark.parametrize("field", ["payload", "secret", "token", "credentials"])
def test_secret_and_credential_extras_are_rejected(field: str):
    with pytest.raises(ValidationError):
        NormalizationIssue(
            field_name="task_type",
            code="invalid",
            message="invalid task type",
            severity="error",
            **{field: "forbidden"},
        )


def test_normalized_output_remains_a_valid_workload_request():
    normalized = normalize_gateway_request(envelope()).normalized_request
    assert isinstance(normalized, WorkloadRequest)
    assert WorkloadRequest.model_validate(normalized.model_dump()) == normalized
