from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import field_validator, model_validator

from mercury.contracts.base import ContractModel
from mercury.contracts.workload_request import WorkloadRequest
from mercury.gateway.identity import GatewayIdentity
from mercury.gateway.session import SessionRequestBinding


class GatewaySecurityCode(str, Enum):
    IDENTITY_MISMATCH = "identity_mismatch"
    TENANT_MISMATCH = "tenant_mismatch"
    UNAUTHORIZED_SESSION = "unauthorized_session"
    SECRET_METADATA = "secret_metadata"
    INVALID_PRIVACY = "invalid_privacy"
    CROSS_TENANT_CONTEXT = "cross_tenant_context"


class GatewaySecurityIssue(ContractModel):
    code: GatewaySecurityCode
    field_name: str
    message: str
    severity: Literal["error", "warning"]

    @field_validator("field_name", "message")
    @classmethod
    def evidence_is_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("security issue evidence must be non-empty")
        return value


class GatewaySecurityResult(ContractModel):
    request_id: str
    workload_id: str
    session_id: str
    tenant_id: str
    allowed: bool
    issues: tuple[GatewaySecurityIssue, ...]

    @field_validator("request_id", "workload_id", "session_id", "tenant_id")
    @classmethod
    def identity_is_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("security identity must be non-empty")
        return value

    @model_validator(mode="after")
    def outcome_and_issues_are_consistent(self) -> GatewaySecurityResult:
        errors = tuple(issue for issue in self.issues if issue.severity == "error")
        if self.allowed and errors:
            raise ValueError("allowed security result cannot contain error issues")
        if not self.allowed and not errors:
            raise ValueError("rejected security result requires explicit error evidence")
        return self


def _walk_metadata(value: object, path: str) -> list[tuple[str, object]]:
    entries: list[tuple[str, object]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            entries.append((child_path, child))
            entries.extend(_walk_metadata(child, child_path))
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            entries.extend(_walk_metadata(child, f"{path}[{index}]"))
    return entries


def evaluate_gateway_security(
    *,
    identity: GatewayIdentity,
    workload_request: WorkloadRequest,
    session_binding: SessionRequestBinding,
    tenant_id: str,
    session_authorized: bool,
) -> GatewaySecurityResult:
    issues: list[GatewaySecurityIssue] = []

    if identity.workload_id != workload_request.workload_id:
        issues.append(
            GatewaySecurityIssue(
                code=GatewaySecurityCode.IDENTITY_MISMATCH,
                field_name="workload_id",
                message="gateway and workload identities do not match",
                severity="error",
            )
        )
    if identity.session_id != workload_request.session_id:
        issues.append(
            GatewaySecurityIssue(
                code=GatewaySecurityCode.IDENTITY_MISMATCH,
                field_name="session_id",
                message="gateway and workload session identities do not match",
                severity="error",
            )
        )
    if (
        session_binding.request_id != identity.request_id
        or session_binding.workload_id != identity.workload_id
        or session_binding.session_identity.session_id != identity.session_id
    ):
        issues.append(
            GatewaySecurityIssue(
                code=GatewaySecurityCode.IDENTITY_MISMATCH,
                field_name="session_binding",
                message="session binding identity is inconsistent",
                severity="error",
            )
        )
    if session_binding.session_identity.tenant_id != tenant_id:
        issues.append(
            GatewaySecurityIssue(
                code=GatewaySecurityCode.TENANT_MISMATCH,
                field_name="tenant_id",
                message="session tenant does not match gateway tenant",
                severity="error",
            )
        )
    if not session_authorized:
        issues.append(
            GatewaySecurityIssue(
                code=GatewaySecurityCode.UNAUTHORIZED_SESSION,
                field_name="session_binding",
                message="session binding is not authorized",
                severity="error",
            )
        )

    sensitive_markers = ("token", "credential", "secret", "api_key")
    metadata_entries = (
        *_walk_metadata(workload_request.input, "input"),
        *_walk_metadata(workload_request.context, "context"),
    )
    for field_path, _ in metadata_entries:
        key = field_path.rsplit(".", 1)[-1].lower()
        if any(marker in key for marker in sensitive_markers):
            issues.append(
                GatewaySecurityIssue(
                    code=GatewaySecurityCode.SECRET_METADATA,
                    field_name=field_path,
                    message="secret, token, or credential metadata is forbidden",
                    severity="error",
                )
            )

    allowed_privacy_levels = {"public", "internal", "confidential", "restricted"}
    if workload_request.privacy_level not in allowed_privacy_levels:
        issues.append(
            GatewaySecurityIssue(
                code=GatewaySecurityCode.INVALID_PRIVACY,
                field_name="privacy_level",
                message="privacy declaration is not recognized",
                severity="error",
            )
        )

    for field_path, value in _walk_metadata(workload_request.context, "context"):
        key = field_path.rsplit(".", 1)[-1].lower()
        if key in {"tenant_id", "context_tenant_id"} and value != tenant_id:
            issues.append(
                GatewaySecurityIssue(
                    code=GatewaySecurityCode.CROSS_TENANT_CONTEXT,
                    field_name=field_path,
                    message="context reference belongs to another tenant",
                    severity="error",
                )
            )

    return GatewaySecurityResult(
        request_id=identity.request_id,
        workload_id=identity.workload_id,
        session_id=identity.session_id,
        tenant_id=tenant_id,
        allowed=not issues,
        issues=tuple(issues),
    )
