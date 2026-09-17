import pytest
from pydantic import ValidationError

from mercury.disaggregated_execution.contracts import (
    MAX_DEPENDENCIES_PER_SEGMENT,
    MAX_EXECUTION_ARTIFACTS_PER_SEGMENT,
    MAX_HANDOFFS_PER_SEGMENT,
    MAX_RETRY_ATTEMPTS,
    MAX_SEGMENTS_PER_EXECUTION_PLAN,
    ExecutionFailureCategory,
    ExecutionHandoffKind,
    ExecutionHandoffState,
    ExecutionRetryPolicy,
    ExecutionSegmentState,
    ExecutionSegmentType,
)


def test_exact_enums_and_limits():
    assert {x.value for x in ExecutionSegmentType} == {
        "PREFILL","DECODE","TOOL_EXECUTION","RETRIEVAL","TRANSFORM","AGGREGATION"
    }
    assert {x.value for x in ExecutionSegmentState} == {
        "PLANNED","READY","RUNNING","SUCCEEDED","FAILED","CANCELLED"
    }
    assert {x.value for x in ExecutionHandoffKind} == {
        "ARTIFACT","CONTEXT","KV_REFERENCE","CONTROL"
    }
    assert {x.value for x in ExecutionHandoffState} == {
        "PENDING","AVAILABLE","CONSUMED","INVALIDATED"
    }
    assert MAX_SEGMENTS_PER_EXECUTION_PLAN == 256
    assert MAX_DEPENDENCIES_PER_SEGMENT == 64
    assert MAX_HANDOFFS_PER_SEGMENT == 64
    assert MAX_EXECUTION_ARTIFACTS_PER_SEGMENT == 128
    assert MAX_RETRY_ATTEMPTS == 8


def test_retry_policy_limit_and_canonical_categories():
    with pytest.raises(ValidationError):
        ExecutionRetryPolicy(
            retry_policy_id="r",
            max_attempts=9,
            retryable_failure_categories=(),
        )

    policy = ExecutionRetryPolicy(
        retry_policy_id="r",
        max_attempts=2,
        retryable_failure_categories=(
            ExecutionFailureCategory.RUNTIME_FAILURE,
            ExecutionFailureCategory.VERIFICATION_FAILURE,
        ),
    )
    assert policy.max_attempts == 2
