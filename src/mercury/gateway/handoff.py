from __future__ import annotations

from enum import Enum

from pydantic import field_validator, model_validator

from mercury.contracts.base import ContractModel
from mercury.contracts.workload_request import WorkloadRequest
from mercury.gateway.admission import GatewayAdmissionDecision, GatewayAdmissionStatus
from mercury.gateway.constraints import CanonicalConstraint
from mercury.gateway.security import GatewaySecurityResult


class GatewayHandoffStatus(str, Enum):
    READY = "ready"
    BLOCKED = "blocked"


class GatewayHandoffEvidence(ContractModel):
    admission_passed: bool
    security_passed: bool
    normalization_completed: bool
    validation_passed: bool
    session_binding_valid: bool
    constraints_canonicalized: bool
    reasons: tuple[str, ...]

    @field_validator("reasons")
    @classmethod
    def reasons_are_non_empty(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if any(not value.strip() for value in values):
            raise ValueError("handoff reasons must be non-empty")
        return values

    @model_validator(mode="after")
    def evidence_and_reasons_are_consistent(self) -> GatewayHandoffEvidence:
        all_passed = all(
            (
                self.admission_passed,
                self.security_passed,
                self.normalization_completed,
                self.validation_passed,
                self.session_binding_valid,
                self.constraints_canonicalized,
            )
        )
        if all_passed and self.reasons:
            raise ValueError("successful handoff evidence cannot contain rejection reasons")
        if not all_passed and not self.reasons:
            raise ValueError("blocked handoff evidence requires explicit reasons")
        return self


class GatewayHandoff(ContractModel):
    handoff_id: str
    request_id: str
    workload_id: str
    session_id: str
    status: GatewayHandoffStatus
    normalized_request: WorkloadRequest | None
    canonical_constraints: tuple[CanonicalConstraint, ...]
    admission_decision_id: str | None
    security_allowed: bool
    evidence: GatewayHandoffEvidence

    @field_validator(
        "handoff_id", "request_id", "workload_id", "session_id", "admission_decision_id"
    )
    @classmethod
    def identity_is_non_empty_when_present(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("handoff identity must be non-empty")
        return value

    @model_validator(mode="after")
    def status_matches_evidence(self) -> GatewayHandoff:
        all_passed = all(
            (
                self.evidence.admission_passed,
                self.evidence.security_passed,
                self.evidence.normalization_completed,
                self.evidence.validation_passed,
                self.evidence.session_binding_valid,
                self.evidence.constraints_canonicalized,
            )
        )
        if self.status is GatewayHandoffStatus.READY:
            if not all_passed or self.evidence.reasons:
                raise ValueError("ready handoff requires every gateway stage to pass")
            if self.normalized_request is None or self.admission_decision_id is None:
                raise ValueError("ready handoff requires admission request evidence")
            if not self.security_allowed:
                raise ValueError("ready handoff requires security approval")
        elif not self.evidence.reasons:
            raise ValueError("blocked handoff requires explicit reasons")
        return self


def build_gateway_handoff(
    *,
    handoff_id: str,
    request_id: str,
    workload_id: str,
    session_id: str,
    admission_decision: GatewayAdmissionDecision | None,
    security_result: GatewaySecurityResult | None,
) -> GatewayHandoff:
    reasons: list[str] = []

    if admission_decision is None:
        admission_passed = False
        normalization_completed = False
        validation_passed = False
        session_binding_valid = False
        constraints_canonicalized = False
        reasons.append("admission evidence is missing")
    else:
        admission_passed = admission_decision.status is GatewayAdmissionStatus.ACCEPTED
        normalization_completed = admission_decision.evidence.normalization_completed
        validation_passed = admission_decision.evidence.validation_passed
        session_binding_valid = admission_decision.evidence.session_binding_valid
        constraints_canonicalized = admission_decision.evidence.constraints_canonicalized
        if not admission_passed:
            reasons.append("gateway admission failed")
            reasons.extend(admission_decision.evidence.reasons)

    if security_result is None:
        security_passed = False
        reasons.append("security evidence is missing")
    else:
        security_passed = security_result.allowed
        if not security_passed:
            reasons.append("gateway security evaluation failed")
            reasons.extend(issue.message for issue in security_result.issues)

    expected_identity = (request_id, workload_id, session_id)
    if admission_decision is not None and (
        admission_decision.request_id,
        admission_decision.workload_id,
        admission_decision.session_id,
    ) != expected_identity:
        admission_passed = False
        reasons.append("admission identity is inconsistent")
    if security_result is not None and (
        security_result.request_id,
        security_result.workload_id,
        security_result.session_id,
    ) != expected_identity:
        security_passed = False
        reasons.append("security identity is inconsistent")

    normalized_request = (
        admission_decision.normalized_request if admission_decision is not None else None
    )
    if normalized_request is not None and (
        normalized_request.workload_id != workload_id
        or normalized_request.session_id != session_id
    ):
        admission_passed = False
        normalization_completed = False
        reasons.append("normalized request identity is inconsistent")

    evidence = GatewayHandoffEvidence(
        admission_passed=admission_passed,
        security_passed=security_passed,
        normalization_completed=normalization_completed,
        validation_passed=validation_passed,
        session_binding_valid=session_binding_valid,
        constraints_canonicalized=constraints_canonicalized,
        reasons=tuple(reasons),
    )
    status = (
        GatewayHandoffStatus.READY
        if all(
            (
                admission_passed,
                security_passed,
                normalization_completed,
                validation_passed,
                session_binding_valid,
                constraints_canonicalized,
            )
        )
        else GatewayHandoffStatus.BLOCKED
    )
    return GatewayHandoff(
        handoff_id=handoff_id,
        request_id=request_id,
        workload_id=workload_id,
        session_id=session_id,
        status=status,
        normalized_request=normalized_request,
        canonical_constraints=(
            admission_decision.canonical_constraints
            if admission_decision is not None
            else ()
        ),
        admission_decision_id=(
            admission_decision.decision_id if admission_decision is not None else None
        ),
        security_allowed=security_result.allowed if security_result is not None else False,
        evidence=evidence,
    )
