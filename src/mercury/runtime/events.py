from __future__ import annotations

from enum import Enum

from pydantic import Field, field_validator, model_validator

from mercury.contracts.base import ContractModel
from mercury.runtime.recovery_state import FailureCategory, RecoveryAction
from mercury.runtime.state import RuntimeNodeStatus


class RuntimeEventType(str, Enum):
    NODE_STARTED = "node_started"
    NODE_COMPLETED = "node_completed"
    NODE_FAILED = "node_failed"
    RETRY_SCHEDULED = "retry_scheduled"
    FALLBACK_SELECTED = "fallback_selected"
    CHECKPOINT_CREATED = "checkpoint_created"
    EXECUTION_CANCELLED = "execution_cancelled"
    RECOVERY_ACTION_APPLIED = "recovery_action_applied"


class RuntimeStateTransition(ContractModel):
    transition_id: str
    execution_id: str
    node_id: str
    from_status: RuntimeNodeStatus
    to_status: RuntimeNodeStatus
    event_type: RuntimeEventType
    attempt: int = Field(ge=0)
    reason: str | None = None

    @field_validator("transition_id", "execution_id", "node_id", "reason")
    @classmethod
    def text_is_non_empty_when_present(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("transition evidence must be non-empty")
        return value

    @model_validator(mode="after")
    def event_has_required_target_status(self) -> RuntimeStateTransition:
        required_targets = {
            RuntimeEventType.NODE_STARTED: RuntimeNodeStatus.RUNNING,
            RuntimeEventType.NODE_COMPLETED: RuntimeNodeStatus.COMPLETED,
            RuntimeEventType.NODE_FAILED: RuntimeNodeStatus.FAILED,
            RuntimeEventType.EXECUTION_CANCELLED: RuntimeNodeStatus.CANCELLED,
        }
        required = required_targets.get(self.event_type)
        if required is not None and self.to_status is not required:
            raise ValueError(f"{self.event_type.value} requires {required.value} target status")
        return self


class RuntimeEventEvidence(ContractModel):
    event_id: str
    trace_id: str
    span_id: str
    execution_id: str
    node_id: str
    event_type: RuntimeEventType
    transition: RuntimeStateTransition
    recovery_action: RecoveryAction | None = None
    failure_category: FailureCategory | None = None
    checkpoint_id: str | None = None

    @field_validator(
        "event_id", "trace_id", "span_id", "execution_id", "node_id", "checkpoint_id"
    )
    @classmethod
    def ids_are_non_empty_when_present(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("event evidence ids must be non-empty")
        return value

    @model_validator(mode="after")
    def evidence_is_consistent_and_complete(self) -> RuntimeEventEvidence:
        if self.transition.execution_id != self.execution_id:
            raise ValueError("transition execution identity does not match event")
        if self.transition.node_id != self.node_id:
            raise ValueError("transition node identity does not match event")
        if self.transition.event_type is not self.event_type:
            raise ValueError("transition event type does not match event")
        recovery_events = {
            RuntimeEventType.RETRY_SCHEDULED,
            RuntimeEventType.FALLBACK_SELECTED,
            RuntimeEventType.RECOVERY_ACTION_APPLIED,
        }
        if self.event_type in recovery_events and self.recovery_action is None:
            raise ValueError("recovery event requires an explicit recovery action")
        if self.event_type is RuntimeEventType.CHECKPOINT_CREATED and not self.checkpoint_id:
            raise ValueError("checkpoint event requires a checkpoint id")
        if self.event_type is RuntimeEventType.NODE_FAILED and self.failure_category is None:
            raise ValueError("failed node event requires a failure category")
        return self
