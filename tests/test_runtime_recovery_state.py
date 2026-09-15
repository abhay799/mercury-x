from __future__ import annotations

import pytest
from pydantic import ValidationError

from mercury.runtime.recovery_state import (
    CheckpointReference,
    ExecutionRecoveryState,
    FailureCategory,
    FailureRecord,
    RecoveryAction,
    RetryRecord,
)


def make_state(**overrides: object) -> ExecutionRecoveryState:
    values: dict[str, object] = {
        "workload_id": "workload-1",
        "execution_id": "execution-1",
        "graph_version": "mercury.execution-graph/v1",
        "current_node_id": "node-1",
        "completed_node_ids": (),
        "pending_node_ids": ("node-1", "node-2"),
        "failed_node_ids": (),
        "context_artifact_ids": ("context-1",),
        "model_configuration_ids": ("model-config-1",),
        "hardware_placement_ids": ("placement-1",),
        "retry_history": (),
        "failure_history": (),
        "checkpoint_references": (),
    }
    values.update(overrides)
    return ExecutionRecoveryState(**values)


def test_valid_initial_recovery_state():
    state = make_state()
    assert state.current_node_id == "node-1"
    assert state.pending_node_ids == ("node-1", "node-2")


@pytest.mark.parametrize("field", ["workload_id", "execution_id"])
def test_blank_workload_or_execution_identity_is_rejected(field: str):
    with pytest.raises(ValidationError):
        make_state(**{field: " "})


def test_completed_and_pending_node_overlap_is_rejected():
    with pytest.raises(ValidationError):
        make_state(completed_node_ids=("node-1",))


def test_completed_and_failed_node_overlap_is_rejected():
    with pytest.raises(ValidationError):
        make_state(completed_node_ids=("node-2",), failed_node_ids=("node-2",))


def test_pending_and_failed_node_overlap_is_rejected():
    with pytest.raises(ValidationError):
        make_state(failed_node_ids=("node-2",))


@pytest.mark.parametrize("field", ["completed_node_ids", "failed_node_ids"])
def test_current_node_cannot_already_be_completed_or_failed(field: str):
    with pytest.raises(ValidationError):
        make_state(**{field: ("node-1",)})


def test_negative_retry_attempt_is_rejected():
    with pytest.raises(ValidationError):
        RetryRecord(node_id="node-1", attempt=-1, action=RecoveryAction.RETRY)


def test_duplicate_checkpoint_ids_are_rejected():
    checkpoint = CheckpointReference(
        checkpoint_id="checkpoint-1", node_id="node-1", reference_uri="mercury://checkpoint/1"
    )
    with pytest.raises(ValidationError):
        make_state(checkpoint_references=(checkpoint, checkpoint))


def test_histories_and_state_containers_are_immutable():
    state = make_state(retry_history=(RetryRecord(node_id="node-1", attempt=0, action=RecoveryAction.RETRY),))
    assert isinstance(state.pending_node_ids, tuple)
    assert isinstance(state.retry_history, tuple)
    with pytest.raises((AttributeError, TypeError, ValidationError)):
        state.pending_node_ids += ("node-3",)


def test_recovery_and_failure_evidence_preserves_explicit_action_and_category():
    retry = RetryRecord(node_id="node-1", attempt=1, action=RecoveryAction.FALLBACK)
    failure = FailureRecord(
        node_id="node-1",
        category=FailureCategory.RUNTIME_FAILURE,
        action=RecoveryAction.FAIL_SAFE,
    )
    state = make_state(retry_history=(retry,), failure_history=(failure,))
    assert state.retry_history[0].action is RecoveryAction.FALLBACK
    assert state.failure_history[0].category is FailureCategory.RUNTIME_FAILURE
    assert state.failure_history[0].action is RecoveryAction.FAIL_SAFE
