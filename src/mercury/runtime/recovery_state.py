from __future__ import annotations

from enum import Enum
from urllib.parse import urlparse

from pydantic import Field, field_validator, model_validator

from mercury.contracts.base import ContractModel


class FailureCategory(str, Enum):
    RUNTIME_FAILURE = "runtime_failure"
    EXECUTION_FAILURE = "execution_failure"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    TIMEOUT = "timeout"
    INTEGRITY_FAILURE = "integrity_failure"
    POLICY_DENIAL = "policy_denial"
    CANCELLED = "cancelled"


class RecoveryAction(str, Enum):
    RETRY = "retry"
    FALLBACK = "fallback"
    RECOMPILE = "recompile"
    RESCHEDULE = "reschedule"
    MIGRATE = "migrate"
    DEGRADE = "degrade"
    ABSTAIN = "abstain"
    FAIL_SAFE = "fail_safe"


class RetryRecord(ContractModel):
    node_id: str
    attempt: int = Field(ge=0)
    action: RecoveryAction

    @field_validator("node_id")
    @classmethod
    def node_id_is_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("node id must be non-empty")
        return value


class FailureRecord(ContractModel):
    node_id: str
    category: FailureCategory
    action: RecoveryAction

    @field_validator("node_id")
    @classmethod
    def node_id_is_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("node id must be non-empty")
        return value


class CheckpointReference(ContractModel):
    checkpoint_id: str
    node_id: str
    reference_uri: str

    @field_validator("checkpoint_id", "node_id")
    @classmethod
    def identifiers_are_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("identifier must be non-empty")
        return value

    @field_validator("reference_uri")
    @classmethod
    def reference_uri_is_opaque_and_credential_free(cls, value: str) -> str:
        if not value or any(character.isspace() for character in value):
            raise ValueError("reference uri must not contain whitespace")
        parsed = urlparse(value)
        if not parsed.scheme or not parsed.path or parsed.query or parsed.fragment or parsed.username or parsed.password:
            raise ValueError("reference uri must be opaque and credential-free")
        return value


class ExecutionRecoveryState(ContractModel):
    workload_id: str
    execution_id: str
    graph_version: str
    current_node_id: str | None = None
    completed_node_ids: tuple[str, ...] = ()
    pending_node_ids: tuple[str, ...] = ()
    failed_node_ids: tuple[str, ...] = ()
    context_artifact_ids: tuple[str, ...] = ()
    model_configuration_ids: tuple[str, ...] = ()
    hardware_placement_ids: tuple[str, ...] = ()
    retry_history: tuple[RetryRecord, ...] = ()
    failure_history: tuple[FailureRecord, ...] = ()
    checkpoint_references: tuple[CheckpointReference, ...] = ()

    @field_validator("workload_id", "execution_id", "graph_version", "current_node_id")
    @classmethod
    def identifiers_are_non_empty(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("identifier must be non-empty")
        return value

    @field_validator(
        "completed_node_ids",
        "pending_node_ids",
        "failed_node_ids",
        "context_artifact_ids",
        "model_configuration_ids",
        "hardware_placement_ids",
    )
    @classmethod
    def collection_ids_are_non_empty(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if any(not value.strip() for value in values):
            raise ValueError("collection ids must be non-empty")
        return values

    @model_validator(mode="after")
    def node_sets_are_disjoint(self) -> ExecutionRecoveryState:
        completed = set(self.completed_node_ids)
        pending = set(self.pending_node_ids)
        failed = set(self.failed_node_ids)
        if completed & pending:
            raise ValueError("completed and pending nodes must not overlap")
        if completed & failed:
            raise ValueError("completed and failed nodes must not overlap")
        if pending & failed:
            raise ValueError("pending and failed nodes must not overlap")
        if self.current_node_id in completed or self.current_node_id in failed:
            raise ValueError("current node cannot be completed or failed")
        checkpoint_ids = tuple(reference.checkpoint_id for reference in self.checkpoint_references)
        if len(checkpoint_ids) != len(set(checkpoint_ids)):
            raise ValueError("checkpoint ids must be unique")
        return self
