from __future__ import annotations

import pytest
from pydantic import ValidationError

from mercury.contracts.workload_request import WorkloadRequest
from mercury.gateway.admission import (
    GatewayAdmissionDecision,
    GatewayAdmissionEvidence,
    GatewayAdmissionStatus,
)
from mercury.gateway.constraints import CanonicalConstraint, ConstraintKind
from mercury.gateway.handoff import GatewayHandoff, GatewayHandoffStatus, build_gateway_handoff
from mercury.gateway.security import (
    GatewaySecurityCode,
    GatewaySecurityIssue,
    GatewaySecurityResult,
)


def request() -> WorkloadRequest:
    return WorkloadRequest(
        workload_id="workload-1",
        session_id="session-1",
        task_type="inference",
        input={"prompt_reference": "mercury://input/1"},
        context={},
        latency_target_ms=100.0,
        quality_target=0.9,
        cost_budget=1.0,
        privacy_level="confidential",
        priority=50,
        hardware_constraints=[],
    )


def constraints() -> tuple[CanonicalConstraint, ...]:
    return (
        CanonicalConstraint(
            constraint_id="workload-1:latency",
            kind=ConstraintKind.LATENCY,
            operator="less_than_or_equal",
            value=100.0,
            unit="ms",
            required=True,
            source_field="latency_target_ms",
        ),
    )


def admission(accepted: bool = True) -> GatewayAdmissionDecision:
    reasons = () if accepted else ("gateway validation failed",)
    return GatewayAdmissionDecision(
        decision_id="admission-1",
        request_id="request-1",
        workload_id="workload-1",
        session_id="session-1",
        status=(
            GatewayAdmissionStatus.ACCEPTED
            if accepted
            else GatewayAdmissionStatus.REJECTED
        ),
        normalized_request=request(),
        canonical_constraints=constraints(),
        evidence=GatewayAdmissionEvidence(
            normalization_completed=accepted,
            validation_passed=accepted,
            session_binding_valid=accepted,
            idempotency_valid=accepted,
            constraints_canonicalized=accepted,
            reasons=reasons,
        ),
    )


def security(allowed: bool = True, **identity_overrides: object) -> GatewaySecurityResult:
    values: dict[str, object] = {
        "request_id": "request-1",
        "workload_id": "workload-1",
        "session_id": "session-1",
        "tenant_id": "tenant-1",
    }
    values.update(identity_overrides)
    issues = ()
    if not allowed:
        issues = (
            GatewaySecurityIssue(
                code=GatewaySecurityCode.UNAUTHORIZED_SESSION,
                field_name="session_binding",
                message="session is not authorized",
                severity="error",
            ),
        )
    return GatewaySecurityResult(allowed=allowed, issues=issues, **values)


def build(**overrides: object) -> GatewayHandoff:
    values: dict[str, object] = {
        "handoff_id": "handoff-1",
        "request_id": "request-1",
        "workload_id": "workload-1",
        "session_id": "session-1",
        "admission_decision": admission(),
        "security_result": security(),
    }
    values.update(overrides)
    return build_gateway_handoff(**values)


def test_valid_gateway_evidence_produces_ready_handoff():
    assert build().status is GatewayHandoffStatus.READY


def test_admission_failure_produces_blocked_handoff():
    assert build(admission_decision=admission(False)).status is GatewayHandoffStatus.BLOCKED


def test_security_failure_produces_blocked_handoff():
    assert build(security_result=security(False)).status is GatewayHandoffStatus.BLOCKED


def test_missing_required_evidence_produces_blocked_handoff():
    assert build(security_result=None).status is GatewayHandoffStatus.BLOCKED


def test_identity_mismatch_is_rejected():
    handoff = build(security_result=security(workload_id="workload-2"))
    assert handoff.status is GatewayHandoffStatus.BLOCKED
    assert any("identity" in reason for reason in handoff.evidence.reasons)


def test_blocked_handoff_has_explicit_reason():
    handoff = build(security_result=security(False))
    assert handoff.evidence.reasons


def test_ready_handoff_has_no_rejection_reason():
    assert build().evidence.reasons == ()


def test_normalized_request_is_preserved():
    decision = admission()
    handoff = build(admission_decision=decision)
    assert handoff.normalized_request is decision.normalized_request


def test_canonical_constraints_are_preserved():
    decision = admission()
    handoff = build(admission_decision=decision)
    assert handoff.canonical_constraints == decision.canonical_constraints


def test_admission_decision_identity_is_preserved():
    decision = admission()
    assert build(admission_decision=decision).admission_decision_id == decision.decision_id


def test_handoff_and_evidence_are_immutable():
    handoff = build()
    with pytest.raises((AttributeError, TypeError, ValidationError)):
        handoff.evidence.reasons += ("changed",)


def test_no_model_selection_fields_are_exposed():
    fields = set(GatewayHandoff.model_fields)
    assert not fields.intersection({"selected_model_id", "model_selection"})


def test_no_hardware_selection_fields_are_exposed():
    fields = set(GatewayHandoff.model_fields)
    assert not fields.intersection({"selected_hardware_id", "hardware_selection"})


def test_no_workload_intelligence_properties_are_exposed():
    fields = set(GatewayHandoff.model_fields)
    assert not fields.intersection({"complexity", "modality", "estimated_tokens"})


def test_no_graph_or_scheduler_fields_are_exposed():
    fields = set(GatewayHandoff.model_fields)
    assert not fields.intersection(
        {"execution_graph", "execution_plan", "scheduler", "placement_id"}
    )
