from mercury.disaggregated_execution.contracts import (
    ExecutionHandoffState,
    ExecutionSegment,
    ExecutionSegmentState,
)


def evaluate_segment_readiness(segment, *, segments, handoffs) -> bool:
    if not isinstance(segment, ExecutionSegment):
        raise ValueError("execution segment required")

    by_id = {item.segment_id: item for item in tuple(segments)}
    handoff_by_id = {item.handoff_id: item for item in tuple(handoffs)}

    if segment.execution_state is not ExecutionSegmentState.PLANNED:
        return False

    for dep_id in segment.dependency_segment_ids:
        dep = by_id.get(dep_id)
        if dep is None or dep.execution_state is not ExecutionSegmentState.SUCCEEDED:
            return False

    for handoff_id in segment.required_handoff_ids:
        handoff = handoff_by_id.get(handoff_id)
        if handoff is None:
            return False
        if handoff.consumer_segment_id != segment.segment_id:
            return False
        if handoff.state is not ExecutionHandoffState.AVAILABLE:
            return False

    return True


def transition_segment_state(
    segment: ExecutionSegment,
    target_state: ExecutionSegmentState,
    *,
    retry_policy=None,
    attempt=1,
    verified=False,
) -> ExecutionSegment:
    current = segment.execution_state
    allowed = {
        ExecutionSegmentState.PLANNED: {
            ExecutionSegmentState.READY,
            ExecutionSegmentState.CANCELLED,
        },
        ExecutionSegmentState.READY: {
            ExecutionSegmentState.RUNNING,
            ExecutionSegmentState.CANCELLED,
        },
        ExecutionSegmentState.RUNNING: {
            ExecutionSegmentState.SUCCEEDED,
            ExecutionSegmentState.FAILED,
            ExecutionSegmentState.CANCELLED,
        },
        ExecutionSegmentState.FAILED: {
            ExecutionSegmentState.READY,
        },
    }
    if target_state not in allowed.get(current, set()):
        raise ValueError("forbidden execution state transition")

    if current is ExecutionSegmentState.FAILED and target_state is ExecutionSegmentState.READY:
        if retry_policy is None:
            raise ValueError("retry policy required")
        if attempt > retry_policy.max_attempts:
            raise ValueError("retry attempt exceeds policy")

    if target_state is ExecutionSegmentState.SUCCEEDED and not verified:
        raise ValueError("verification required before success")

    payload = segment.model_dump()
    payload["execution_state"] = target_state
    return ExecutionSegment(**payload)
