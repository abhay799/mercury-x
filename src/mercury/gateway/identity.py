from __future__ import annotations

from pydantic import field_validator

from mercury.contracts.base import ContractModel


class GatewayIdentity(ContractModel):
    request_id: str
    workload_id: str
    session_id: str

    @field_validator("request_id", "workload_id", "session_id")
    @classmethod
    def identity_ids_are_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("gateway identity ids must be non-empty")
        return value
