import pytest

from mercury.disaggregated_execution.contracts import (
    ExecutionRetryPolicy,
    ExecutionFailureCategory,
    ExecutionSegmentState,
)
from mercury.disaggregated_execution.readiness import (
    evaluate_segment_readiness,
    transition_segment_state,
)
from tests._phase12_helpers import make_segment


def test_entry_segment_can_be_ready_without_dependencies():
    segment = make_segment()
    assert evaluate_segment_readiness(segment, segments=(segment,), handoffs=())


def test_success_requires_verification():
    segment = make_segment(state=ExecutionSegmentState.RUNNING)
    with pytest.raises(ValueError):
        transition_segment_state(segment, ExecutionSegmentState.SUCCEEDED, verified=False)


def test_failed_retry_requires_policy_and_limit():
    failed = make_segment(state=ExecutionSegmentState.FAILED)
    policy = ExecutionRetryPolicy(
        retry_policy_id="r",
        max_attempts=2,
        retryable_failure_categories=(ExecutionFailureCategory.RUNTIME_FAILURE,),
    )
    ready = transition_segment_state(
        failed,
        ExecutionSegmentState.READY,
        retry_policy=policy,
        attempt=2,
    )
    assert ready.execution_state is ExecutionSegmentState.READY
    with pytest.raises(ValueError):
        transition_segment_state(
            failed,
            ExecutionSegmentState.READY,
            retry_policy=policy,
            attempt=3,
        )
