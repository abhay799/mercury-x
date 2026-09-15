from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import ValidationError, field_validator, model_validator

from mercury.contracts.base import ContractModel
from mercury.contracts.workload_request import WorkloadRequest
from mercury.gateway.identity import GatewayIdentity


class GatewayValidationCode(str, Enum):
    MISSING_IDENTITY = "missing_identity"
    INVALID_IDENTITY = "invalid_identity"
    MALFORMED_REQUEST = "malformed_request"
    FORBIDDEN_FIELD = "forbidden_field"
    IDENTITY_MISMATCH = "identity_mismatch"


class GatewayValidationIssue(ContractModel):
    code: GatewayValidationCode
    field_name: str
    message: str
    severity: Literal["error", "warning"]

    @field_validator("field_name", "message")
    @classmethod
    def issue_evidence_is_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("validation issue evidence must be non-empty")
        return value


class GatewayValidationResult(ContractModel):
    request_id: str | None
    workload_id: str | None
    session_id: str | None
    accepted: bool
    issues: tuple[GatewayValidationIssue, ...]
    validated_request: WorkloadRequest | None

    @model_validator(mode="after")
    def outcome_and_evidence_are_consistent(self) -> GatewayValidationResult:
        errors = tuple(issue for issue in self.issues if issue.severity == "error")
        if self.accepted and errors:
            raise ValueError("accepted result cannot contain error issues")
        if self.accepted and self.validated_request is None:
            raise ValueError("accepted result requires a validated request")
        if not self.accepted and not errors:
            raise ValueError("rejected result requires explicit error evidence")
        if not self.accepted and self.validated_request is not None:
            raise ValueError("rejected result cannot contain a validated request")
        return self


def _raw_identity_value(identity: GatewayIdentity | dict[str, object], field: str) -> str | None:
    value = getattr(identity, field) if isinstance(identity, GatewayIdentity) else identity.get(field)
    return value if isinstance(value, str) else None


def validate_gateway_request(
    identity: GatewayIdentity | dict[str, object],
    workload_request: WorkloadRequest | dict[str, object],
) -> GatewayValidationResult:
    request_id = _raw_identity_value(identity, "request_id")
    workload_id = _raw_identity_value(identity, "workload_id")
    session_id = _raw_identity_value(identity, "session_id")
    issues: list[GatewayValidationIssue] = []

    try:
        validated_identity = (
            identity
            if isinstance(identity, GatewayIdentity)
            else GatewayIdentity.model_validate(identity)
        )
    except ValidationError as error:
        validated_identity = None
        for item in error.errors():
            issues.append(
                GatewayValidationIssue(
                    code=(
                        GatewayValidationCode.MISSING_IDENTITY
                        if item["type"] == "missing"
                        else GatewayValidationCode.INVALID_IDENTITY
                    ),
                    field_name=str(item["loc"][0]),
                    message=str(item["msg"]),
                    severity="error",
                )
            )

    try:
        validated_request = (
            workload_request
            if isinstance(workload_request, WorkloadRequest)
            else WorkloadRequest.model_validate(workload_request)
        )
    except ValidationError as error:
        validated_request = None
        for item in error.errors():
            issues.append(
                GatewayValidationIssue(
                    code=(
                        GatewayValidationCode.FORBIDDEN_FIELD
                        if item["type"] == "extra_forbidden"
                        else GatewayValidationCode.MALFORMED_REQUEST
                    ),
                    field_name=str(item["loc"][0]),
                    message=str(item["msg"]),
                    severity="error",
                )
            )

    if validated_identity is not None and validated_request is not None:
        if validated_identity.workload_id != validated_request.workload_id:
            issues.append(
                GatewayValidationIssue(
                    code=GatewayValidationCode.IDENTITY_MISMATCH,
                    field_name="workload_id",
                    message="gateway workload identity does not match request",
                    severity="error",
                )
            )
        if validated_identity.session_id != validated_request.session_id:
            issues.append(
                GatewayValidationIssue(
                    code=GatewayValidationCode.IDENTITY_MISMATCH,
                    field_name="session_id",
                    message="gateway session identity does not match request",
                    severity="error",
                )
            )

    accepted = not any(issue.severity == "error" for issue in issues)
    return GatewayValidationResult(
        request_id=request_id,
        workload_id=workload_id,
        session_id=session_id,
        accepted=accepted,
        issues=tuple(issues),
        validated_request=validated_request if accepted else None,
    )
