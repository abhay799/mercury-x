import hashlib
import json

from mercury.disaggregated_execution.contracts import (
    ExecutionFailureCategory,
    ExecutionRetryPolicy,
    SegmentExecutionResult,
    StitchedExecutionResult,
)


def classify_execution_failure(kind: str) -> ExecutionFailureCategory:
    mapping = {
        "input": ExecutionFailureCategory.INPUT_FAILURE,
        "handoff": ExecutionFailureCategory.HANDOFF_FAILURE,
        "compatibility": ExecutionFailureCategory.COMPATIBILITY_FAILURE,
        "runtime": ExecutionFailureCategory.RUNTIME_FAILURE,
        "verification": ExecutionFailureCategory.VERIFICATION_FAILURE,
        "cancelled": ExecutionFailureCategory.CANCELLED_FAILURE,
    }
    try:
        return mapping[kind]
    except KeyError as exc:
        raise ValueError("unknown execution failure kind") from exc


def can_retry_segment(
    failure_category: ExecutionFailureCategory,
    retry_policy: ExecutionRetryPolicy,
    *,
    attempt: int,
) -> bool:
    if attempt >= retry_policy.max_attempts:
        return False
    return failure_category in retry_policy.retryable_failure_categories


def verify_segment_result(result: SegmentExecutionResult) -> bool:
    return bool(result.succeeded and result.verified)


def stitch_execution_results(
    *,
    execution_plan_id,
    namespace_type,
    namespace_id,
    terminal_segment_ids,
    results,
    stitching_policy_id,
) -> StitchedExecutionResult:
    terminal_segment_ids = tuple(sorted(terminal_segment_ids))
    result_by_segment = {result.segment_id: result for result in tuple(results)}

    missing = [segment_id for segment_id in terminal_segment_ids if segment_id not in result_by_segment]
    if missing:
        raise ValueError("missing terminal segment result")

    selected = tuple(result_by_segment[segment_id] for segment_id in terminal_segment_ids)
    if any(not verify_segment_result(result) for result in selected):
        raise ValueError("terminal result not verified")

    terminal_result_ids = tuple(sorted(result.segment_result_id for result in selected))
    artifact_lineage = tuple(
        sorted(
            {
                artifact
                for result in selected
                for artifact in result.output_artifact_ids
            }
        )
    )

    payload = {
        "execution_plan_id": execution_plan_id,
        "namespace_type": namespace_type.value,
        "namespace_id": namespace_id,
        "terminal_segment_ids": list(terminal_segment_ids),
        "terminal_result_ids": list(terminal_result_ids),
        "artifact_lineage": list(artifact_lineage),
        "verification_status": True,
        "stitching_policy_id": stitching_policy_id,
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    result_fingerprint = hashlib.sha256(raw).hexdigest()
    stitched_result_id = hashlib.sha256(
        b"stitched:" + result_fingerprint.encode("ascii")
    ).hexdigest()

    return StitchedExecutionResult(
        stitched_result_id=stitched_result_id,
        execution_plan_id=execution_plan_id,
        namespace_type=namespace_type,
        namespace_id=namespace_id,
        terminal_segment_ids=terminal_segment_ids,
        terminal_result_ids=terminal_result_ids,
        artifact_lineage=artifact_lineage,
        verification_status=True,
        stitching_policy_id=stitching_policy_id,
        result_fingerprint=result_fingerprint,
    )
