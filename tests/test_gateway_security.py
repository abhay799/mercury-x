from __future__ import annotations

import pytest
from pydantic import ValidationError

from mercury.contracts.workload_request import WorkloadRequest
from mercury.gateway.identity import GatewayIdentity
from mercury.gateway.security import (
    GatewaySecurityCode,
    GatewaySecurityResult,
    evaluate_gateway_security,
)
from mercury.gateway.session import (
    IdempotencyKey,
    SessionIdentity,
    SessionRequestBinding,
    bind_gateway_session,
)


def identity(**overrides: object) -> GatewayIdentity:
    values: dict[str, object] = {
        "request_id": "request-1",
        "workload_id": "workload-1",
        "session_id": "session-1",
    }
    values.update(overrides)
    return GatewayIdentity(**values)


def workload(**overrides: object) -> WorkloadRequest:
    values: dict[str, object] = {
        "workload_id": "workload-1",
        "session_id": "session-1",
        "task_type": "inference",
        "input": {"prompt_reference": "mercury://input/1"},
        "context": {"context_reference": "mercury://context/1", "tenant_id": "tenant-1"},
        "latency_target_ms": 100.0,
        "quality_target": 0.9,
        "cost_budget": 1.0,
        "privacy_level": "confidential",
        "priority": 50,
        "hardware_constraints": [],
    }
    values.update(overrides)
    return WorkloadRequest(**values)


def binding(**session_overrides: object) -> SessionRequestBinding:
    session_values: dict[str, object] = {
        "session_id": "session-1",
        "owner_id": "owner-1",
        "tenant_id": "tenant-1",
    }
    session_values.update(session_overrides)
    return bind_gateway_session(
        binding_id="binding-1",
        session_identity=SessionIdentity(**session_values),
        request_id="request-1",
        workload_id="workload-1",
        idempotency_key=IdempotencyKey(value="idempotency-1"),
        request_fingerprint="sha256:" + "a" * 64,
    )


def evaluate(**overrides: object) -> GatewaySecurityResult:
    values: dict[str, object] = {
        "identity": identity(),
        "workload_request": workload(),
        "session_binding": binding(),
        "tenant_id": "tenant-1",
        "session_authorized": True,
    }
    values.update(overrides)
    return evaluate_gateway_security(**values)


def test_valid_secure_gateway_request_is_allowed():
    assert evaluate().allowed is True


def test_tenant_mismatch_is_rejected():
    result = evaluate(tenant_id="tenant-2")
    assert result.allowed is False
    assert any(issue.code is GatewaySecurityCode.TENANT_MISMATCH for issue in result.issues)


def test_session_identity_mismatch_is_rejected():
    result = evaluate(session_binding=binding(session_id="session-2"))
    assert result.allowed is False
    assert any(issue.code is GatewaySecurityCode.IDENTITY_MISMATCH for issue in result.issues)


def test_unauthorized_session_binding_is_rejected():
    result = evaluate(session_authorized=False)
    assert result.allowed is False
    assert any(issue.code is GatewaySecurityCode.UNAUTHORIZED_SESSION for issue in result.issues)


@pytest.mark.parametrize("field", ["token", "credentials", "secret"])
def test_sensitive_metadata_is_rejected(field: str):
    result = evaluate(workload_request=workload(context={field: "forbidden"}))
    assert result.allowed is False
    assert any(issue.code is GatewaySecurityCode.SECRET_METADATA for issue in result.issues)


def test_invalid_privacy_declaration_is_rejected():
    result = evaluate(workload_request=workload(privacy_level="unknown-policy"))
    assert result.allowed is False
    assert any(issue.code is GatewaySecurityCode.INVALID_PRIVACY for issue in result.issues)


def test_cross_tenant_context_reference_is_rejected():
    result = evaluate(
        workload_request=workload(
            context={"context_reference": "mercury://context/2", "tenant_id": "tenant-2"}
        )
    )
    assert result.allowed is False
    assert any(
        issue.code is GatewaySecurityCode.CROSS_TENANT_CONTEXT for issue in result.issues
    )


def test_rejected_result_has_explicit_reason():
    result = evaluate(session_authorized=False)
    assert result.issues
    assert all(issue.message.strip() for issue in result.issues)


def test_accepted_result_has_no_error_issue():
    result = evaluate()
    assert not any(issue.severity == "error" for issue in result.issues)


def test_identity_is_preserved():
    result = evaluate()
    assert (result.request_id, result.workload_id, result.session_id, result.tenant_id) == (
        "request-1",
        "workload-1",
        "session-1",
        "tenant-1",
    )


def test_security_result_and_issues_are_immutable():
    result = evaluate()
    assert isinstance(result.issues, tuple)
    with pytest.raises((AttributeError, TypeError, ValidationError)):
        result.allowed = False


def test_no_model_selection_fields_are_exposed():
    fields = set(GatewaySecurityResult.model_fields)
    assert not fields.intersection({"selected_model_id", "model_selection"})


def test_no_hardware_selection_fields_are_exposed():
    fields = set(GatewaySecurityResult.model_fields)
    assert not fields.intersection({"selected_hardware_id", "hardware_selection"})


def test_no_workload_intelligence_is_inferred():
    fields = set(GatewaySecurityResult.model_fields)
    assert not fields.intersection(
        {"reasoning_complexity", "complexity", "modality", "estimated_tokens"}
    )
