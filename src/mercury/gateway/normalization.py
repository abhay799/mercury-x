from __future__ import annotations

from typing import Literal

from pydantic import ValidationError, field_validator, model_validator

from mercury.contracts.base import ContractModel
from mercury.contracts.workload_request import WorkloadRequest
from mercury.gateway.models import GatewayRequestEnvelope


class NormalizationIssue(ContractModel):
    field_name: str
    code: str
    message: str
    severity: Literal["error", "warning"]

    @field_validator("field_name", "code", "message")
    @classmethod
    def issue_evidence_is_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("normalization issue evidence must be non-empty")
        return value


class NormalizationResult(ContractModel):
    request_id: str
    workload_id: str
    session_id: str
    normalized: bool
    normalized_request: WorkloadRequest | None
    issues: tuple[NormalizationIssue, ...]

    @field_validator("request_id", "workload_id", "session_id")
    @classmethod
    def identity_evidence_is_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("normalization identity must be non-empty")
        return value

    @model_validator(mode="after")
    def outcome_is_explicit_and_consistent(self) -> NormalizationResult:
        if self.normalized and self.normalized_request is None:
            raise ValueError("successful normalization requires a normalized request")
        if not self.normalized and not self.issues:
            raise ValueError("failed normalization requires explicit issue evidence")
        if not self.normalized and self.normalized_request is not None:
            raise ValueError("failed normalization cannot expose a normalized request")
        return self


def normalize_gateway_request(envelope: GatewayRequestEnvelope) -> NormalizationResult:
    request_data = envelope.workload_request.model_dump(mode="python")
    request_data["task_type"] = request_data["task_type"].strip()
    request_data["privacy_level"] = request_data["privacy_level"].strip()

    normalized_constraints: list[str] = []
    seen_constraints: set[str] = set()
    for raw_constraint in request_data["hardware_constraints"]:
        constraint = raw_constraint.strip()
        if not constraint or constraint in seen_constraints:
            continue
        normalized_constraints.append(constraint)
        seen_constraints.add(constraint)
    request_data["hardware_constraints"] = normalized_constraints

    try:
        normalized_request = WorkloadRequest.model_validate(request_data)
    except ValidationError as error:
        issues = tuple(
            NormalizationIssue(
                field_name=str(item["loc"][0]),
                code=str(item["type"]),
                message=str(item["msg"]),
                severity="error",
            )
            for item in error.errors()
        )
        return NormalizationResult(
            request_id=envelope.identity.request_id,
            workload_id=envelope.identity.workload_id,
            session_id=envelope.identity.session_id,
            normalized=False,
            normalized_request=None,
            issues=issues,
        )

    return NormalizationResult(
        request_id=envelope.identity.request_id,
        workload_id=envelope.identity.workload_id,
        session_id=envelope.identity.session_id,
        normalized=True,
        normalized_request=normalized_request,
        issues=(),
    )
