import hashlib
import json

from mercury.disaggregated_execution.contracts import (
    ExecutionSegment,
    ExecutionSegmentState,
    ExecutionSegmentType,
    SegmentExecutionResult,
    make_segment_id,
)
from mercury.global_memory.contracts import GlobalMemoryNamespace


def plan_id():
    return "plan-1"


def make_segment(
    *,
    segment_type=ExecutionSegmentType.PREFILL,
    sequence=1,
    segment_id=None,
    dependencies=(),
    required_handoffs=(),
    produced_handoffs=(),
    state=ExecutionSegmentState.PLANNED,
):
    sid = segment_id or make_segment_id(
        execution_plan_seed=plan_id(),
        segment_type=segment_type,
        creation_sequence=sequence,
        namespace_type=GlobalMemoryNamespace.PROJECT,
        namespace_id="p1",
    )
    return ExecutionSegment(
        segment_id=sid,
        execution_plan_id=plan_id(),
        namespace_type=GlobalMemoryNamespace.PROJECT,
        namespace_id="p1",
        segment_type=segment_type,
        input_artifact_ids=(),
        output_contract_id=f"out-{sequence}",
        dependency_segment_ids=tuple(sorted(dependencies)),
        required_handoff_ids=tuple(sorted(required_handoffs)),
        produced_handoff_ids=tuple(sorted(produced_handoffs)),
        handoff_policy_id="handoff-policy-1",
        retry_policy_id="retry-policy-1",
        verification_policy_id="verify-policy-1",
        creation_sequence=sequence,
        execution_state=state,
    )


def make_segment_result(segment, *, succeeded=True, verified=True, attempt=1):
    artifacts = (f"artifact-{segment.creation_sequence}",)
    payload = {
        "segment_id": segment.segment_id,
        "succeeded": succeeded,
        "verified": verified,
        "artifacts": artifacts,
        "attempt": attempt,
    }
    fp = hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return SegmentExecutionResult(
        segment_result_id=f"result-{segment.creation_sequence}",
        execution_plan_id=segment.execution_plan_id,
        segment_id=segment.segment_id,
        namespace_type=segment.namespace_type,
        namespace_id=segment.namespace_id,
        succeeded=succeeded,
        verified=verified,
        output_artifact_ids=artifacts,
        failure_category=None if succeeded else None,
        attempt=attempt,
        result_fingerprint=fp,
    )
