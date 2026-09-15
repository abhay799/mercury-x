from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import field_validator, model_validator

from mercury.contracts.base import ContractModel
from mercury.contracts.workload_request import WorkloadRequest
from mercury.gateway.identity import GatewayIdentity


class GatewayValidationStatus(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class GatewayValidationEvidence(ContractModel):
    status: GatewayValidationStatus
    reasons: tuple[str, ...]

    @field_validator("reasons")
    @classmethod
    def reasons_are_non_empty(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if any(not value.strip() for value in values):
            raise ValueError("validation reasons must be non-empty")
        return values

    @model_validator(mode="after")
    def status_and_reasons_are_consistent(self) -> GatewayValidationEvidence:
        if self.status is GatewayValidationStatus.REJECTED and not self.reasons:
            raise ValueError("rejected status requires at least one explicit reason")
        if self.status is GatewayValidationStatus.ACCEPTED and self.reasons:
            raise ValueError("accepted status cannot contain rejection reasons")
        return self


class GatewayRequestEnvelope(ContractModel):
    gateway_request_id: str
    identity: GatewayIdentity
    workload_request: WorkloadRequest
    received_at: datetime
    normalized: bool
    validation_status: GatewayValidationStatus
    validation_evidence: GatewayValidationEvidence

    @field_validator("gateway_request_id")
    @classmethod
    def gateway_request_id_is_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("gateway request id must be non-empty")
        return value

    @model_validator(mode="after")
    def identity_and_validation_evidence_are_consistent(self) -> GatewayRequestEnvelope:
        if self.validation_status is not self.validation_evidence.status:
            raise ValueError("validation status does not match validation evidence")
        if self.identity.workload_id != self.workload_request.workload_id:
            raise ValueError("gateway and workload identities do not match")
        if self.identity.session_id != self.workload_request.session_id:
            raise ValueError("gateway and workload sessions do not match")
        return self
