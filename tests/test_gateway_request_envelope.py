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


def workload_request() -> WorkloadRequest:
    return WorkloadRequest(
        workload_id="workload-1",
        session_id="session-1",
        task_type="inference",
        input={"prompt_reference": "mercury://input/1"},
        context={"context_reference": "mercury://context/1"},
        latency_target_ms=100.0,
        quality_target=0.9,
        cost_budget=1.0,
        privacy_level="confidential",
        priority=50,
        hardware_constraints=(),
    )


def identity(**overrides: object) -> GatewayIdentity:
    values: dict[str, object] = {
        "request_id": "request-1",
        "workload_id": "workload-1",
        "session_id": "session-1",
    }
    values.update(overrides)
    return GatewayIdentity(**values)


def evidence(**overrides: object) -> GatewayValidationEvidence:
    values: dict[str, object] = {
        "status": GatewayValidationStatus.ACCEPTED,
        "reasons": (),
    }
    values.update(overrides)
    return GatewayValidationEvidence(**values)


def envelope(**overrides: object) -> GatewayRequestEnvelope:
    values: dict[str, object] = {
        "gateway_request_id": "gateway-request-1",
        "identity": identity(),
        "workload_request": workload_request(),
        "received_at": datetime(2026, 9, 16, 12, 0, tzinfo=UTC),
        "normalized": False,
        "validation_status": GatewayValidationStatus.ACCEPTED,
        "validation_evidence": evidence(),
    }
    values.update(overrides)
    return GatewayRequestEnvelope(**values)


def test_valid_accepted_gateway_envelope():
    assert envelope().validation_status is GatewayValidationStatus.ACCEPTED


def test_valid_rejected_envelope_with_explicit_reason():
    rejected_evidence = evidence(
        status=GatewayValidationStatus.REJECTED,
        reasons=("workload policy validation failed",),
    )
    rejected = envelope(
        validation_status=GatewayValidationStatus.REJECTED,
        validation_evidence=rejected_evidence,
    )
    assert rejected.validation_evidence.reasons == ("workload policy validation failed",)


def test_blank_request_id_is_rejected():
    with pytest.raises(ValidationError):
        identity(request_id=" ")


def test_blank_workload_id_is_rejected():
    with pytest.raises(ValidationError):
        identity(workload_id=" ")


def test_blank_session_id_is_rejected():
    with pytest.raises(ValidationError):
        identity(session_id=" ")


def test_blank_gateway_request_id_is_rejected():
    with pytest.raises(ValidationError):
        envelope(gateway_request_id=" ")


def test_rejected_status_without_reason_is_rejected():
    with pytest.raises(ValidationError):
        evidence(status=GatewayValidationStatus.REJECTED)


def test_accepted_status_with_rejection_reason_is_rejected():
    with pytest.raises(ValidationError):
        evidence(reasons=("unexpected rejection reason",))


def test_identity_is_immutable_after_validation():
    gateway_identity = identity()
    with pytest.raises((AttributeError, TypeError, ValidationError)):
        gateway_identity.request_id = "request-2"


def test_original_workload_request_is_preserved_unchanged():
    original = workload_request()
    before = original.model_dump(mode="python")
    gateway_envelope = envelope(workload_request=original)
    assert gateway_envelope.workload_request is original
    assert original.model_dump(mode="python") == before


@pytest.mark.parametrize("normalized", [True, False])
def test_normalization_flag_is_preserved(normalized: bool):
    assert envelope(normalized=normalized).normalized is normalized


@pytest.mark.parametrize("field", ["payload", "credentials", "token", "secret"])
def test_secret_and_credential_extra_fields_are_rejected(field: str):
    with pytest.raises(ValidationError):
        envelope(**{field: "forbidden"})


def test_gateway_envelope_exposes_no_model_or_hardware_selection_fields():
    fields = set(GatewayRequestEnvelope.model_fields)
    assert "selected_model_id" not in fields
    assert "selected_hardware_id" not in fields
    assert "model_selection" not in fields
    assert "hardware_selection" not in fields
