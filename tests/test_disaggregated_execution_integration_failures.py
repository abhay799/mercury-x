import pytest

from mercury.disaggregated_execution.contracts import (
    ExecutionSegmentState,
    ExecutionSegmentType,
)
from mercury.disaggregated_execution.graph import build_disaggregated_execution_plan
from mercury.disaggregated_execution.integration import apply_prediction_hints
from mercury.global_memory.contracts import GlobalMemoryNamespace
from tests._phase12_helpers import make_segment


def test_prediction_hints_are_advisory_only():
    segment = make_segment()
    plan = build_disaggregated_execution_plan(
        namespace_type=GlobalMemoryNamespace.PROJECT,
        namespace_id="p1",
        source_execution_graph_id="graph-1",
        segments=(segment,),
    )
    hinted = apply_prediction_hints(plan, prediction_ids=("pred-1",))
    assert hinted == plan


def test_cross_namespace_segment_fails_closed():
    segment = make_segment()
    payload = segment.model_dump()
    payload["namespace_id"] = "p2"
    bad = type(segment)(**payload)
    with pytest.raises(ValueError):
        build_disaggregated_execution_plan(
            namespace_type=GlobalMemoryNamespace.PROJECT,
            namespace_id="p1",
            source_execution_graph_id="graph-1",
            segments=(bad,),
        )


def test_cancelled_segment_remains_terminal():
    cancelled = make_segment(state=ExecutionSegmentState.CANCELLED)
    assert cancelled.execution_state is ExecutionSegmentState.CANCELLED


def test_prefill_decode_shape_is_representable():
    prefill = make_segment(
        segment_type=ExecutionSegmentType.PREFILL,
        sequence=1,
    )
    decode = make_segment(
        segment_type=ExecutionSegmentType.DECODE,
        sequence=2,
        dependencies=(prefill.segment_id,),
    )
    plan = build_disaggregated_execution_plan(
        namespace_type=GlobalMemoryNamespace.PROJECT,
        namespace_id="p1",
        source_execution_graph_id="graph-1",
        segments=(prefill, decode),
    )
    assert plan.entry_segment_ids == (prefill.segment_id,)
    assert plan.terminal_segment_ids == (decode.segment_id,)
