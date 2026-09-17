import hashlib
import json

from mercury.disaggregated_execution.contracts import (
    MAX_SEGMENTS_PER_EXECUTION_PLAN,
    DisaggregatedExecutionPlan,
    ExecutionSegment,
    make_execution_plan_id,
)


def _cycle_free(segments: tuple[ExecutionSegment, ...]) -> bool:
    by_id = {s.segment_id: s for s in segments}
    visiting = set()
    visited = set()

    def visit(segment_id: str):
        if segment_id in visited:
            return
        if segment_id in visiting:
            raise ValueError("execution segment graph contains cycle")
        visiting.add(segment_id)
        for dep in by_id[segment_id].dependency_segment_ids:
            visit(dep)
        visiting.remove(segment_id)
        visited.add(segment_id)

    for segment_id in sorted(by_id):
        visit(segment_id)
    return True


def build_disaggregated_execution_plan(
    *,
    namespace_type,
    namespace_id,
    source_execution_graph_id,
    segments,
    handoffs=(),
    plan_version="1",
    creation_sequence=1,
) -> DisaggregatedExecutionPlan:
    segments = tuple(segments)
    handoffs = tuple(handoffs)
    if not segments:
        raise ValueError("execution plan requires at least one segment")
    if len(segments) > MAX_SEGMENTS_PER_EXECUTION_PLAN:
        raise ValueError("too many execution segments")

    ids = [segment.segment_id for segment in segments]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate execution segment")

    by_id = {segment.segment_id: segment for segment in segments}
    for segment in segments:
        if segment.namespace_type is not namespace_type or segment.namespace_id != namespace_id:
            raise ValueError("segment namespace mismatch")
        for dep in segment.dependency_segment_ids:
            if dep not in by_id:
                raise ValueError("dangling execution dependency")

    _cycle_free(segments)

    consumers = {dep for segment in segments for dep in segment.dependency_segment_ids}
    entry = tuple(sorted(s.segment_id for s in segments if not s.dependency_segment_ids))
    terminal = tuple(sorted(s.segment_id for s in segments if s.segment_id not in consumers))
    if not entry or not terminal:
        raise ValueError("execution plan requires entry and terminal segments")

    execution_plan_id = make_execution_plan_id(
        namespace_type=namespace_type,
        namespace_id=namespace_id,
        source_execution_graph_id=source_execution_graph_id,
        plan_version=plan_version,
    )

    for handoff in handoffs:
        if handoff.execution_plan_id != execution_plan_id:
            raise ValueError("handoff execution plan mismatch")
        if handoff.producer_segment_id not in by_id or handoff.consumer_segment_id not in by_id:
            raise ValueError("handoff endpoint not declared")
        if handoff.namespace_type is not namespace_type or handoff.namespace_id != namespace_id:
            raise ValueError("handoff namespace mismatch")

    ordered_segments = tuple(sorted(segments, key=lambda s: (s.creation_sequence, s.segment_id)))
    ordered_handoffs = tuple(sorted(handoffs, key=lambda h: (h.creation_sequence, h.handoff_id)))

    payload = {
        "execution_plan_id": execution_plan_id,
        "namespace_type": namespace_type.value,
        "namespace_id": namespace_id,
        "source_execution_graph_id": source_execution_graph_id,
        "segments": [s.model_dump(mode="json") for s in ordered_segments],
        "handoffs": [h.model_dump(mode="json") for h in ordered_handoffs],
        "entry_segment_ids": list(entry),
        "terminal_segment_ids": list(terminal),
        "creation_sequence": creation_sequence,
        "plan_version": plan_version,
    }
    plan_fingerprint = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()

    return DisaggregatedExecutionPlan(
        execution_plan_id=execution_plan_id,
        namespace_type=namespace_type,
        namespace_id=namespace_id,
        source_execution_graph_id=source_execution_graph_id,
        segments=ordered_segments,
        handoffs=ordered_handoffs,
        entry_segment_ids=entry,
        terminal_segment_ids=terminal,
        creation_sequence=creation_sequence,
        plan_version=plan_version,
        plan_fingerprint=plan_fingerprint,
    )
