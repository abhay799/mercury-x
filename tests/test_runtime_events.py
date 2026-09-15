from __future__ import annotations

import pytest
from pydantic import ValidationError

from mercury.runtime.events import RuntimeEventEvidence, RuntimeEventType, RuntimeStateTransition
from mercury.runtime.recovery_state import FailureCategory, RecoveryAction
from mercury.runtime.state import RuntimeNodeStatus


def transition(**overrides: object) -> RuntimeStateTransition:
    values: dict[str, object] = {
        "transition_id": "transition-1",
        "execution_id": "execution-1",
        "node_id": "node-1",
        "from_status": RuntimeNodeStatus.PENDING,
        "to_status": RuntimeNodeStatus.RUNNING,
        "event_type": RuntimeEventType.NODE_STARTED,
        "attempt": 0,
        "reason": "node admitted",
    }
    values.update(overrides)
    return RuntimeStateTransition(**values)


def evidence(**overrides: object) -> RuntimeEventEvidence:
    values: dict[str, object] = {
        "event_id": "event-1",
        "trace_id": "trace-1",
        "span_id": "span-1",
        "execution_id": "execution-1",
        "node_id": "node-1",
        "event_type": RuntimeEventType.NODE_STARTED,
        "transition": transition(),
        "recovery_action": None,
        "failure_category": None,
        "checkpoint_id": None,
    }
    values.update(overrides)
    return RuntimeEventEvidence(**values)


def test_valid_runtime_transition():
    assert transition().to_status is RuntimeNodeStatus.RUNNING


@pytest.mark.parametrize("field", ["transition_id", "execution_id", "node_id"])
def test_blank_transition_ids_are_rejected(field: str):
    with pytest.raises(ValidationError):
        transition(**{field: " "})


@pytest.mark.parametrize("field", ["event_id", "trace_id", "span_id", "execution_id", "node_id"])
def test_blank_event_evidence_ids_are_rejected(field: str):
    with pytest.raises(ValidationError):
        evidence(**{field: " "})


def test_negative_attempt_is_rejected():
    with pytest.raises(ValidationError):
        transition(attempt=-1)


@pytest.mark.parametrize(
    ("event_type", "required_status"),
    [
        (RuntimeEventType.NODE_STARTED, RuntimeNodeStatus.RUNNING),
        (RuntimeEventType.NODE_COMPLETED, RuntimeNodeStatus.COMPLETED),
        (RuntimeEventType.NODE_FAILED, RuntimeNodeStatus.FAILED),
        (RuntimeEventType.EXECUTION_CANCELLED, RuntimeNodeStatus.CANCELLED),
    ],
)
def test_terminal_node_events_require_matching_target_status(
    event_type: RuntimeEventType, required_status: RuntimeNodeStatus
):
    with pytest.raises(ValidationError):
        transition(event_type=event_type, to_status=RuntimeNodeStatus.PENDING)
    assert transition(event_type=event_type, to_status=required_status).to_status is required_status


@pytest.mark.parametrize(
    ("event_type", "action"),
    [
        (RuntimeEventType.RETRY_SCHEDULED, RecoveryAction.RETRY),
        (RuntimeEventType.FALLBACK_SELECTED, RecoveryAction.FALLBACK),
        (RuntimeEventType.RECOVERY_ACTION_APPLIED, RecoveryAction.MIGRATE),
    ],
)
def test_recovery_events_preserve_explicit_recovery_action(
    event_type: RuntimeEventType, action: RecoveryAction
):
    event_transition = transition(event_type=event_type)
    event = evidence(event_type=event_type, transition=event_transition, recovery_action=action)
    assert event.recovery_action is action


def test_checkpoint_event_requires_checkpoint_id():
    event_transition = transition(event_type=RuntimeEventType.CHECKPOINT_CREATED)
    with pytest.raises(ValidationError):
        evidence(event_type=RuntimeEventType.CHECKPOINT_CREATED, transition=event_transition)


def test_contracts_are_immutable():
    event = evidence()
    with pytest.raises((AttributeError, TypeError, ValidationError)):
        event.transition.reason = "changed"


@pytest.mark.parametrize("field", ["payload", "api_key", "token", "credentials"])
def test_payload_and_secret_extra_fields_are_rejected(field: str):
    with pytest.raises(ValidationError):
        evidence(**{field: "forbidden"})


def test_event_evidence_preserves_execution_trace_and_node_identity():
    event = evidence(failure_category=FailureCategory.RUNTIME_FAILURE)
    assert event.execution_id == "execution-1"
    assert event.trace_id == "trace-1"
    assert event.node_id == "node-1"
