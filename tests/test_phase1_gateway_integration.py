from __future__ import annotations

from datetime import UTC, datetime

import pytest

from mercury.contracts.workload_request import WorkloadRequest
from mercury.gateway.admission import GatewayAdmissionStatus, evaluate_gateway_admission
from mercury.gateway.constraints import (
    CanonicalConstraint,
    ConstraintKind,
    canonicalize_gateway_constraints,
)
from mercury.gateway.handoff import GatewayHandoff, GatewayHandoffStatus, build_gateway_handoff
from mercury.gateway.identity import GatewayIdentity
from mercury.gateway.models import (
    GatewayRequestEnvelope,
    GatewayValidationEvidence,
    GatewayValidationStatus,
)
from mercury.gateway.normalization import normalize_gateway_request
from mercury.gateway.security import evaluate_gateway_security
from mercury.gateway.session import (
    IdempotencyKey,
    SessionIdentity,
    bind_gateway_session,
)
from mercury.gateway.validation import validate_gateway_request


FINGERPRINT = "sha256:" + "a" * 64


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


def build_valid_pipeline(*, existing_bindings: tuple = ()) -> dict[str, object]:
    original = workload()
    gateway_identity = identity()
    gateway_envelope = envelope(original)
    normalization = normalize_gateway_request(gateway_envelope)
    assert normalization.normalized_request is not None
    validation = validate_gateway_request(gateway_identity, normalization.normalized_request)
    binding = bind_gateway_session(
        binding_id="binding-1",
        session_identity=SessionIdentity(
            session_id="session-1", owner_id="owner-1", tenant_id="tenant-1"
        ),
        request_id="request-1",
        workload_id="workload-1",
        idempotency_key=IdempotencyKey(value="idempotency-1"),
        request_fingerprint=FINGERPRINT,
        existing_bindings=existing_bindings,
    )
    constraints = canonicalize_gateway_constraints(
        gateway_identity, normalization.normalized_request
    )
    admission = evaluate_gateway_admission(
        decision_id="admission-1",
        request_id="request-1",
        workload_id="workload-1",
        session_id="session-1",
        normalization_result=normalization,
        validation_result=validation,
        session_binding=binding,
        idempotency_valid=True,
        constraint_result=constraints,
    )
    security = evaluate_gateway_security(
        identity=gateway_identity,
        workload_request=normalization.normalized_request,
        session_binding=binding,
        tenant_id="tenant-1",
        session_authorized=True,
    )
    handoff = build_gateway_handoff(
        handoff_id="handoff-1",
        request_id="request-1",
        workload_id="workload-1",
        session_id="session-1",
        admission_decision=admission,
        security_result=security,
    )
    return {
        "original": original,
        "identity": gateway_identity,
        "envelope": gateway_envelope,
        "normalization": normalization,
        "validation": validation,
        "binding": binding,
        "constraints": constraints,
        "admission": admission,
        "security": security,
        "handoff": handoff,
    }


def rebuild_handoff(
    pipeline: dict[str, object], *, admission=None, security=None
) -> GatewayHandoff:
    return build_gateway_handoff(
        handoff_id="handoff-1",
        request_id="request-1",
        workload_id="workload-1",
        session_id="session-1",
        admission_decision=admission if admission is not None else pipeline["admission"],
        security_result=security if security is not None else pipeline["security"],
    )


def test_fully_valid_request_produces_ready_gateway_handoff():
    assert build_valid_pipeline()["handoff"].status is GatewayHandoffStatus.READY


def test_identity_remains_identical_end_to_end():
    pipeline = build_valid_pipeline()
    expected = ("request-1", "workload-1", "session-1")
    assert (
        pipeline["handoff"].request_id,
        pipeline["handoff"].workload_id,
        pipeline["handoff"].session_id,
    ) == expected
    assert (
        pipeline["admission"].request_id,
        pipeline["admission"].workload_id,
        pipeline["admission"].session_id,
    ) == expected


def test_normalized_workload_request_semantics_are_preserved():
    pipeline = build_valid_pipeline()
    original = pipeline["original"]
    normalized = pipeline["normalization"].normalized_request
    assert normalized.input == original.input
    assert normalized.context == original.context
    assert normalized.latency_target_ms == original.latency_target_ms
    assert normalized.quality_target == original.quality_target
    assert normalized.cost_budget == original.cost_budget


def test_validation_failure_prevents_ready_handoff():
    pipeline = build_valid_pipeline()
    invalid = {**pipeline["original"].model_dump(), "latency_target_ms": 0}
    validation = validate_gateway_request(identity(), invalid)
    admission = evaluate_gateway_admission(
        decision_id="admission-failed-validation",
        request_id="request-1",
        workload_id="workload-1",
        session_id="session-1",
        normalization_result=pipeline["normalization"],
        validation_result=validation,
        session_binding=pipeline["binding"],
        idempotency_valid=True,
        constraint_result=pipeline["constraints"],
    )
    assert rebuild_handoff(pipeline, admission=admission).status is GatewayHandoffStatus.BLOCKED


def test_idempotency_conflict_prevents_ready_handoff():
    pipeline = build_valid_pipeline()
    with pytest.raises(ValueError, match="fingerprint"):
        bind_gateway_session(
            binding_id="binding-2",
            session_identity=pipeline["binding"].session_identity,
            request_id="request-1",
            workload_id="workload-1",
            idempotency_key=IdempotencyKey(value="idempotency-1"),
            request_fingerprint="sha256:" + "b" * 64,
            existing_bindings=(pipeline["binding"],),
        )
    admission = evaluate_gateway_admission(
        decision_id="admission-idempotency-conflict",
        request_id="request-1",
        workload_id="workload-1",
        session_id="session-1",
        normalization_result=pipeline["normalization"],
        validation_result=pipeline["validation"],
        session_binding=pipeline["binding"],
        idempotency_valid=False,
        constraint_result=pipeline["constraints"],
    )
    assert rebuild_handoff(pipeline, admission=admission).status is GatewayHandoffStatus.BLOCKED


def test_session_tenant_mismatch_prevents_ready_handoff():
    pipeline = build_valid_pipeline()
    security = evaluate_gateway_security(
        identity=pipeline["identity"],
        workload_request=pipeline["normalization"].normalized_request,
        session_binding=pipeline["binding"],
        tenant_id="tenant-2",
        session_authorized=True,
    )
    assert rebuild_handoff(pipeline, security=security).status is GatewayHandoffStatus.BLOCKED


def test_conflicting_constraints_prevent_ready_handoff():
    pipeline = build_valid_pipeline()
    first = CanonicalConstraint(
        constraint_id="custom-1",
        kind=ConstraintKind.CAPABILITY,
        operator="equals",
        value="runtime-a",
        unit=None,
        required=True,
        source_field="hardware_constraints",
    )
    conflict = first.model_copy(update={"value": "runtime-b"})
    constraints = canonicalize_gateway_constraints(
        pipeline["identity"],
        pipeline["normalization"].normalized_request,
        additional_constraints=(first, conflict),
    )
    admission = evaluate_gateway_admission(
        decision_id="admission-constraint-conflict",
        request_id="request-1",
        workload_id="workload-1",
        session_id="session-1",
        normalization_result=pipeline["normalization"],
        validation_result=pipeline["validation"],
        session_binding=pipeline["binding"],
        idempotency_valid=True,
        constraint_result=constraints,
    )
    assert rebuild_handoff(pipeline, admission=admission).status is GatewayHandoffStatus.BLOCKED


def test_security_rejection_prevents_ready_handoff():
    pipeline = build_valid_pipeline()
    insecure = workload(context={"token": "forbidden", "tenant_id": "tenant-1"})
    security = evaluate_gateway_security(
        identity=pipeline["identity"],
        workload_request=insecure,
        session_binding=pipeline["binding"],
        tenant_id="tenant-1",
        session_authorized=True,
    )
    assert rebuild_handoff(pipeline, security=security).status is GatewayHandoffStatus.BLOCKED


def test_cross_tenant_context_violation_fails_closed():
    pipeline = build_valid_pipeline()
    cross_tenant = workload(context={"tenant_id": "tenant-2"})
    security = evaluate_gateway_security(
        identity=pipeline["identity"],
        workload_request=cross_tenant,
        session_binding=pipeline["binding"],
        tenant_id="tenant-1",
        session_authorized=True,
    )
    handoff = rebuild_handoff(pipeline, security=security)
    assert security.allowed is False
    assert handoff.status is GatewayHandoffStatus.BLOCKED


def test_normalized_request_is_preserved_into_handoff():
    pipeline = build_valid_pipeline()
    assert pipeline["handoff"].normalized_request is pipeline["normalization"].normalized_request


def test_canonical_constraints_are_preserved_into_handoff():
    pipeline = build_valid_pipeline()
    assert pipeline["handoff"].canonical_constraints == pipeline["constraints"].constraints


def test_admission_evidence_is_preserved():
    pipeline = build_valid_pipeline()
    assert pipeline["handoff"].evidence.admission_passed is True
    assert pipeline["handoff"].admission_decision_id == pipeline["admission"].decision_id


def test_security_evidence_is_preserved():
    pipeline = build_valid_pipeline()
    assert pipeline["handoff"].security_allowed is pipeline["security"].allowed
    assert pipeline["handoff"].evidence.security_passed is pipeline["security"].allowed


def test_deterministic_idempotent_replay_produces_equivalent_outcome():
    first = build_valid_pipeline()
    replay = build_valid_pipeline(existing_bindings=(first["binding"],))
    assert replay["binding"] is first["binding"]
    assert replay["handoff"] == first["handoff"]


def test_no_model_selection_fields_appear():
    fields = set(GatewayHandoff.model_fields)
    assert not fields.intersection({"selected_model_id", "model_selection"})


def test_no_hardware_selection_fields_appear():
    fields = set(GatewayHandoff.model_fields)
    assert not fields.intersection({"selected_hardware_id", "hardware_selection"})


def test_no_workload_intelligence_properties_are_inferred():
    fields = set(GatewayHandoff.model_fields)
    assert not fields.intersection({"complexity", "modality", "estimated_tokens"})


def test_no_execution_graph_scheduler_or_runtime_objects_are_created():
    pipeline = build_valid_pipeline()
    fields = set(GatewayHandoff.model_fields)
    assert not fields.intersection(
        {"execution_graph", "execution_plan", "scheduler", "runtime", "placement_id"}
    )
    assert all("execution_graph" not in type(value).__name__.lower() for value in pipeline.values())
