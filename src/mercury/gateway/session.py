from __future__ import annotations

from pydantic import field_validator, model_validator

from mercury.contracts.base import ContractModel


class SessionIdentity(ContractModel):
    session_id: str
    owner_id: str
    tenant_id: str

    @field_validator("session_id", "owner_id", "tenant_id")
    @classmethod
    def identity_fields_are_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("session identity fields must be non-empty")
        return value


class IdempotencyKey(ContractModel):
    value: str

    @field_validator("value")
    @classmethod
    def value_is_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("idempotency key must be non-empty")
        return value


class IdempotencyRecord(ContractModel):
    idempotency_key: IdempotencyKey
    request_id: str
    workload_id: str
    session_id: str
    request_fingerprint: str

    @field_validator("request_id", "workload_id", "session_id", "request_fingerprint")
    @classmethod
    def record_evidence_is_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("idempotency record evidence must be non-empty")
        return value


class SessionRequestBinding(ContractModel):
    binding_id: str
    session_identity: SessionIdentity
    request_id: str
    workload_id: str
    idempotency_record: IdempotencyRecord

    @field_validator("binding_id", "request_id", "workload_id")
    @classmethod
    def binding_evidence_is_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("session binding evidence must be non-empty")
        return value

    @model_validator(mode="after")
    def linked_identities_are_consistent(self) -> SessionRequestBinding:
        if self.request_id != self.idempotency_record.request_id:
            raise ValueError("request identity does not match idempotency record")
        if self.workload_id != self.idempotency_record.workload_id:
            raise ValueError("workload identity does not match idempotency record")
        if self.session_identity.session_id != self.idempotency_record.session_id:
            raise ValueError("session identity does not match idempotency record")
        return self


def bind_gateway_session(
    *,
    binding_id: str,
    session_identity: SessionIdentity,
    request_id: str,
    workload_id: str,
    idempotency_key: IdempotencyKey,
    request_fingerprint: str,
    existing_bindings: tuple[SessionRequestBinding, ...] = (),
) -> SessionRequestBinding:
    for existing in existing_bindings:
        if existing.session_identity.session_id == session_identity.session_id and (
            existing.session_identity.owner_id != session_identity.owner_id
            or existing.session_identity.tenant_id != session_identity.tenant_id
        ):
            raise ValueError("session owner/tenant identity cannot change")
        if (
            existing.workload_id == workload_id
            and existing.session_identity.session_id != session_identity.session_id
        ):
            raise ValueError("workload cannot rebind to another session")
        if existing.idempotency_record.idempotency_key == idempotency_key:
            if existing.idempotency_record.request_fingerprint != request_fingerprint:
                raise ValueError("idempotency key has a different request fingerprint")
            if (
                existing.request_id != request_id
                or existing.workload_id != workload_id
                or existing.session_identity != session_identity
            ):
                raise ValueError("idempotency replay identity does not match existing binding")
            return existing

    record = IdempotencyRecord(
        idempotency_key=idempotency_key,
        request_id=request_id,
        workload_id=workload_id,
        session_id=session_identity.session_id,
        request_fingerprint=request_fingerprint,
    )
    return SessionRequestBinding(
        binding_id=binding_id,
        session_identity=session_identity,
        request_id=request_id,
        workload_id=workload_id,
        idempotency_record=record,
    )
