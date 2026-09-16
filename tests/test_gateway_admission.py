from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from mercury.contracts.workload_request import WorkloadRequest
from mercury.gateway.admission import (
    GatewayAdmissionDecision,
    GatewayAdmissionStatus,
    evaluate_gateway_admission,
)
from mercury.gateway.constraints import (
    CanonicalConstraint,
    ConstraintKind,
    canonicalize_gateway_constraints,
)
from mercury.gateway.identity import GatewayIdentity
from mercury.gateway.models import (
    GatewayRequestEnvelope,
    GatewayValidationEvidence,
    GatewayValidationStatus,
)
from mercury.gateway.normalization import normalize_gateway_request
from mercury.gateway.session import IdempotencyKey, SessionIdentity, bind_gateway_session
from mercury.gateway.validation import validate_gateway_request


FINGERPRINT = "sha256:" + "a" * 64


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
        "hardware_constraints": ["cpu"],
    }
    values.update(overrides)
    return WorkloadRequest(**values)


def identity() -> GatewayIdentity:
    return GatewayIdentity(
        request_id="request-1", workload_id="workload-1", session_id="session-1"
    )


def envelope(request: WorkloadRequest) -> GatewayRequestEnvelope:
    return GatewayRequestEnvelope(
        gateway_request_id="gateway-request-1",
        identity=identity(),
        workload_request=request,
        received_at=datetime(2026, 9, 16, 12, 0, tzinfo=UTC),
        normalized=False,
        validation_status=GatewayValidationStatus.ACCEPTED,
        validation_evidence=GatewayValidationEvidence(
            status=GatewayValidationStatus.ACCEPTED, reasons=()
        ),
    )


def valid_pipeline() -> dict[str, object]:
    request = workload()
    gateway_identity = identity()
    normalization = normalize_gateway_request(envelope(request))
    assert normalization.normalized_request is not None
    validation = validate_gateway_request(
        gateway_identity, normalization.normalized_request
    )
    binding = bind_gateway_session(
        binding_id="binding-1",
        session_identity=SessionIdentity(
            session_id="session-1", owner_id="owner-1", tenant_id="tenant-1"
        ),
        request_id="request-1",
        workload_id="workload-1",
        idempotency_key=IdempotencyKey(value="idempotency-1"),
        request_fingerprint=FINGERPRINT,
    )
    constraints = canonicalize_gateway_constraints(
        gateway_identity, normalization.normalized_request
    )
    return {
        "decision_id": "admission-1",
        "request_id": "request-1",
        "workload_id": "workload-1",
        "session_id": "session-1",
        "normalization_result": normalization,
        "validation_result": validation,
        "session_binding": binding,
        "idempotency_valid": True,
        "constraint_result": constraints,
    }


def evaluate(**overrides: object) -> GatewayAdmissionDecision:
    values = valid_pipeline()
    values.update(overrides)
    return evaluate_gateway_admission(**values)


def test_fully_valid_gateway_request_is_accepted():
    assert evaluate().status is GatewayAdmissionStatus.ACCEPTED


def test_normalization_failure_causes_reject():
    failed = normalize_gateway_request(envelope(workload(task_type=" ")))
    assert evaluate(normalization_result=failed).status is GatewayAdmissionStatus.REJECTED


def test_validation_failure_causes_reject():
    failed = validate_gateway_request(identity(), {**workload().model_dump(), "latency_target_ms": 0})
    assert evaluate(validation_result=failed).status is GatewayAdmissionStatus.REJECTED


def test_session_binding_failure_causes_reject():
    assert evaluate(session_binding=None).status is GatewayAdmissionStatus.REJECTED


def test_idempotency_conflict_causes_reject():
    assert evaluate(idempotency_valid=False).status is GatewayAdmissionStatus.REJECTED


def test_constraint_conflict_causes_reject():
    base = CanonicalConstraint(
        constraint_id="custom-1",
        kind=ConstraintKind.CAPABILITY,
        operator="equals",
        value="runtime-a",
        unit=None,
        required=True,
        source_field="hardware_constraints",
    )
    conflict = base.model_copy(update={"value": "runtime-b"})
    normalized_request = valid_pipeline()["normalization_result"].normalized_request
    result = canonicalize_gateway_constraints(
        identity(), normalized_request, additional_constraints=(base, conflict)
    )
    assert evaluate(constraint_result=result).status is GatewayAdmissionStatus.REJECTED


def test_missing_required_evidence_causes_reject():
    assert evaluate(normalization_result=None).status is GatewayAdmissionStatus.REJECTED


def test_rejected_decision_has_explicit_reason():
    decision = evaluate(idempotency_valid=False)
    assert decision.evidence.reasons
    assert all(reason.strip() for reason in decision.evidence.reasons)


def test_accepted_decision_has_no_rejection_reason():
    assert evaluate().evidence.reasons == ()


def test_request_workload_and_session_identity_remains_consistent():
    decision = evaluate()
    assert (decision.request_id, decision.workload_id, decision.session_id) == (
        "request-1",
        "workload-1",
        "session-1",
    )


def test_normalized_workload_request_is_preserved():
    pipeline = valid_pipeline()
    decision = evaluate_gateway_admission(**pipeline)
    assert decision.normalized_request is pipeline["normalization_result"].normalized_request


def test_canonical_constraints_are_preserved():
    pipeline = valid_pipeline()
    decision = evaluate_gateway_admission(**pipeline)
    assert decision.canonical_constraints == pipeline["constraint_result"].constraints


def test_admission_decision_and_evidence_are_immutable():
    decision = evaluate()
    with pytest.raises((AttributeError, TypeError, ValidationError)):
        decision.evidence.reasons += ("changed",)


def test_no_model_selection_fields_are_exposed():
    fields = set(GatewayAdmissionDecision.model_fields)
    assert not fields.intersection({"selected_model_id", "model_selection"})


def test_no_hardware_selection_fields_are_exposed():
    fields = set(GatewayAdmissionDecision.model_fields)
    assert not fields.intersection({"selected_hardware_id", "hardware_selection"})


def test_no_workload_intelligence_properties_are_inferred():
    fields = set(GatewayAdmissionDecision.model_fields)
    assert not fields.intersection(
        {"reasoning_complexity", "complexity", "modality", "estimated_tokens"}
    )
