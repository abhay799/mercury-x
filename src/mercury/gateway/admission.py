from __future__ import annotations

from enum import Enum

from pydantic import field_validator, model_validator

from mercury.contracts.base import ContractModel
from mercury.contracts.workload_request import WorkloadRequest
from mercury.gateway.constraints import CanonicalConstraint, ConstraintNormalizationResult
from mercury.gateway.normalization import NormalizationResult
from mercury.gateway.session import SessionRequestBinding
from mercury.gateway.validation import GatewayValidationResult


class GatewayAdmissionStatus(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class GatewayAdmissionEvidence(ContractModel):
    normalization_completed: bool
    validation_passed: bool
    session_binding_valid: bool
    idempotency_valid: bool
    constraints_canonicalized: bool
    reasons: tuple[str, ...]

    @field_validator("reasons")
    @classmethod
    def reasons_are_non_empty(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if any(not value.strip() for value in values):
            raise ValueError("admission reasons must be non-empty")
        return values

    @model_validator(mode="after")
    def stage_outcome_has_consistent_reasons(self) -> GatewayAdmissionEvidence:
        all_passed = all(
            (
                self.normalization_completed,
                self.validation_passed,
                self.session_binding_valid,
                self.idempotency_valid,
                self.constraints_canonicalized,
            )
        )
        if all_passed and self.reasons:
            raise ValueError("successful admission evidence cannot contain rejection reasons")
        if not all_passed and not self.reasons:
            raise ValueError("failed admission evidence requires explicit reasons")
        return self


class GatewayAdmissionDecision(ContractModel):
    decision_id: str
    request_id: str
    workload_id: str
    session_id: str
    status: GatewayAdmissionStatus
    normalized_request: WorkloadRequest | None
    canonical_constraints: tuple[CanonicalConstraint, ...]
    evidence: GatewayAdmissionEvidence

    @field_validator("decision_id", "request_id", "workload_id", "session_id")
    @classmethod
    def identity_is_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("admission identity must be non-empty")
        return value

    @model_validator(mode="after")
    def status_matches_evidence(self) -> GatewayAdmissionDecision:
        all_passed = all(
            (
                self.evidence.normalization_completed,
                self.evidence.validation_passed,
                self.evidence.session_binding_valid,
                self.evidence.idempotency_valid,
                self.evidence.constraints_canonicalized,
            )
        )
        if self.status is GatewayAdmissionStatus.ACCEPTED:
            if not all_passed or self.evidence.reasons:
                raise ValueError("accepted decision requires every stage to pass")
            if self.normalized_request is None:
                raise ValueError("accepted decision requires a normalized request")
        elif not self.evidence.reasons:
            raise ValueError("rejected decision requires explicit reasons")
        return self


def evaluate_gateway_admission(
    *,
    decision_id: str,
    request_id: str,
    workload_id: str,
    session_id: str,
    normalization_result: NormalizationResult | None,
    validation_result: GatewayValidationResult | None,
    session_binding: SessionRequestBinding | None,
    idempotency_valid: bool | None,
    constraint_result: ConstraintNormalizationResult | None,
) -> GatewayAdmissionDecision:
    reasons: list[str] = []

    normalization_completed = (
        normalization_result is not None and normalization_result.normalized
    )
    if normalization_result is None:
        reasons.append("normalization evidence is missing")
    elif not normalization_result.normalized:
        reasons.append("normalization did not complete")

    validation_passed = validation_result is not None and validation_result.accepted
    if validation_result is None:
        reasons.append("validation evidence is missing")
    elif not validation_result.accepted:
        reasons.append("gateway validation failed")

    session_binding_valid = session_binding is not None
    if session_binding is None:
        reasons.append("session binding evidence is missing or invalid")

    idempotency_stage_valid = idempotency_valid is True
    if idempotency_valid is None:
        reasons.append("idempotency evidence is missing")
    elif not idempotency_valid:
        reasons.append("idempotency conflict detected")

    constraints_canonicalized = (
        constraint_result is not None and constraint_result.canonicalized
    )
    if constraint_result is None:
        reasons.append("constraint canonicalization evidence is missing")
    elif not constraint_result.canonicalized:
        reasons.append("constraint canonicalization failed")

    expected_identity = (request_id, workload_id, session_id)
    if normalization_result is not None and (
        normalization_result.request_id,
        normalization_result.workload_id,
        normalization_result.session_id,
    ) != expected_identity:
        normalization_completed = False
        reasons.append("normalization identity is inconsistent")
    if validation_result is not None and (
        validation_result.request_id,
        validation_result.workload_id,
        validation_result.session_id,
    ) != expected_identity:
        validation_passed = False
        reasons.append("validation identity is inconsistent")
    if session_binding is not None and (
        session_binding.request_id,
        session_binding.workload_id,
        session_binding.session_identity.session_id,
    ) != expected_identity:
        session_binding_valid = False
        reasons.append("session binding identity is inconsistent")
    if constraint_result is not None and (
        constraint_result.request_id,
        constraint_result.workload_id,
        constraint_result.session_id,
    ) != expected_identity:
        constraints_canonicalized = False
        reasons.append("constraint identity is inconsistent")

    normalized_request = (
        normalization_result.normalized_request
        if normalization_result is not None
        else None
    )
    if (
        normalized_request is not None
        and validation_result is not None
        and validation_result.validated_request is not None
        and validation_result.validated_request != normalized_request
    ):
        validation_passed = False
        reasons.append("validated request does not match normalized request")

    evidence = GatewayAdmissionEvidence(
        normalization_completed=normalization_completed,
        validation_passed=validation_passed,
        session_binding_valid=session_binding_valid,
        idempotency_valid=idempotency_stage_valid,
        constraints_canonicalized=constraints_canonicalized,
        reasons=tuple(reasons),
    )
    status = (
        GatewayAdmissionStatus.ACCEPTED
        if all(
            (
                normalization_completed,
                validation_passed,
                session_binding_valid,
                idempotency_stage_valid,
                constraints_canonicalized,
            )
        )
        else GatewayAdmissionStatus.REJECTED
    )
    return GatewayAdmissionDecision(
        decision_id=decision_id,
        request_id=request_id,
        workload_id=workload_id,
        session_id=session_id,
        status=status,
        normalized_request=normalized_request,
        canonical_constraints=(
            constraint_result.constraints if constraint_result is not None else ()
        ),
        evidence=evidence,
    )
