from __future__ import annotations

from enum import Enum
from typing import Literal
from urllib.parse import urlparse

from pydantic import Field, field_validator

from mercury.contracts.base import ContractModel


class ContextArtifactKind(str, Enum):
    INPUT_CONTEXT = "input_context"
    SESSION_CONTEXT = "session_context"
    RETRIEVAL_CONTEXT = "retrieval_context"
    MODEL_STATE = "model_state"
    KV_STATE = "kv_state"
    TOOL_STATE = "tool_state"
    EXECUTION_STATE = "execution_state"
    INTERMEDIATE_RESULT = "intermediate_result"
    CHECKPOINT = "checkpoint"
    SHARED_ARTIFACT = "shared_artifact"


class ContextPortability(str, Enum):
    PORTABLE = "portable"
    MODEL_SPECIFIC = "model_specific"
    RUNTIME_SPECIFIC = "runtime_specific"


class ContextStorageTier(str, Enum):
    ACCELERATOR_MEMORY = "accelerator_memory"
    SYSTEM_RAM = "system_ram"
    LOCAL_NVME = "local_nvme"
    DISTRIBUTED_CACHE = "distributed_cache"
    OBJECT_STORAGE = "object_storage"
    ARCHIVE = "archive"


class ContextArtifact(ContractModel):
    schema_version: Literal["mercury.context.artifact/v1"] = "mercury.context.artifact/v1"
    artifact_id: str
    owner_id: str
    tenant_id: str
    authorized_owner_ids: tuple[str, ...]
    authorized_tenant_ids: tuple[str, ...]
    kind: ContextArtifactKind
    portability: ContextPortability
    storage_tier: ContextStorageTier
    privacy_level: str
    reference_uri: str
    integrity_evidence: str | None = None
    model_id: str | None = None
    runtime_id: str | None = None

    @field_validator(
        "artifact_id", "owner_id", "tenant_id", "privacy_level", "model_id", "runtime_id"
    )
    @classmethod
    def identifiers_are_non_empty(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("value must be non-empty")
        return value

    @field_validator("authorized_owner_ids", "authorized_tenant_ids")
    @classmethod
    def authorization_ids_are_non_empty(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if not values or any(not value.strip() for value in values):
            raise ValueError("authorization ids must be non-empty")
        return values

    @field_validator("reference_uri")
    @classmethod
    def reference_uri_is_opaque_and_credential_free(cls, value: str) -> str:
        if not value or any(character.isspace() for character in value):
            raise ValueError("reference uri must not contain whitespace")
        parsed = urlparse(value)
        if not parsed.scheme or not parsed.path or parsed.query or parsed.fragment or parsed.username or parsed.password:
            raise ValueError("reference uri must be opaque and credential-free")
        return value


class ContextReuseRequest(ContractModel):
    schema_version: Literal["mercury.context.reuse-request/v1"] = "mercury.context.reuse-request/v1"
    artifact_id: str
    requester_owner_id: str
    requester_tenant_id: str
    privacy_level: str
    model_id: str | None = None
    runtime_id: str | None = None

    @field_validator("artifact_id", "requester_owner_id", "requester_tenant_id", "privacy_level")
    @classmethod
    def required_identifiers_are_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must be non-empty")
        return value


class ContextReuseDecision(ContractModel):
    schema_version: Literal["mercury.context.reuse-decision/v1"] = "mercury.context.reuse-decision/v1"
    artifact_id: str
    allowed: bool
    reasons: tuple[str, ...] = Field(min_length=1)

    @field_validator("artifact_id")
    @classmethod
    def artifact_id_is_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("artifact id must be non-empty")
        return value

    @field_validator("reasons")
    @classmethod
    def reasons_are_non_empty(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if any(not value.strip() for value in values):
            raise ValueError("reasons must be non-empty")
        return values
