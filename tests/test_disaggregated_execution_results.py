import pytest

from mercury.disaggregated_execution.contracts import (
    ExecutionFailureCategory,
    ExecutionRetryPolicy,
    ExecutionSegmentState,
)
from mercury.disaggregated_execution.results import (
    can_retry_segment,
    classify_execution_failure,
    stitch_execution_results,
)
from tests._phase12_helpers import make_segment, make_segment_result


def test_failure_classification_and_retry_policy():
    category = classify_execution_failure("runtime")
    assert category is ExecutionFailureCategory.RUNTIME_FAILURE
    policy = ExecutionRetryPolicy(
        retry_policy_id="r",
        max_attempts=3,
        retryable_failure_categories=(ExecutionFailureCategory.RUNTIME_FAILURE,),
    )
    assert can_retry_segment(category, policy, attempt=1)
    assert not can_retry_segment(category, policy, attempt=3)


def test_stitching_is_deterministic_and_requires_all_terminal_results():
    a = make_segment(state=ExecutionSegmentState.SUCCEEDED)
    result = make_segment_result(a)
    stitched1 = stitch_execution_results(
        execution_plan_id=a.execution_plan_id,
        namespace_type=a.namespace_type,
        namespace_id=a.namespace_id,
        terminal_segment_ids=(a.segment_id,),
        results=(result,),
        stitching_policy_id="stitch-1",
    )
    stitched2 = stitch_execution_results(
        execution_plan_id=a.execution_plan_id,
        namespace_type=a.namespace_type,
        namespace_id=a.namespace_id,
        terminal_segment_ids=(a.segment_id,),
        results=(result,),
        stitching_policy_id="stitch-1",
    )
    assert stitched1 == stitched2
    with pytest.raises(ValueError):
        stitch_execution_results(
            execution_plan_id=a.execution_plan_id,
            namespace_type=a.namespace_type,
            namespace_id=a.namespace_id,
            terminal_segment_ids=(a.segment_id, "missing"),
            results=(result,),
            stitching_policy_id="stitch-1",
        )
