import pytest

from mercury.disaggregated_execution.graph import build_disaggregated_execution_plan
from mercury.disaggregated_execution.contracts import ExecutionSegmentType
from mercury.global_memory.contracts import GlobalMemoryNamespace
from tests._phase12_helpers import make_segment


def test_builds_deterministic_entry_and_terminal_sets():
    a = make_segment(sequence=1)
    b = make_segment(
        segment_type=ExecutionSegmentType.DECODE,
        sequence=2,
        dependencies=(a.segment_id,),
    )
    first = build_disaggregated_execution_plan(
        namespace_type=GlobalMemoryNamespace.PROJECT,
        namespace_id="p1",
        source_execution_graph_id="graph-1",
        segments=(b, a),
    )
    second = build_disaggregated_execution_plan(
        namespace_type=GlobalMemoryNamespace.PROJECT,
        namespace_id="p1",
        source_execution_graph_id="graph-1",
        segments=(a, b),
    )
    assert first == second
    assert first.entry_segment_ids == (a.segment_id,)
    assert first.terminal_segment_ids == (b.segment_id,)


def test_dangling_dependency_fails_closed():
    bad = make_segment(dependencies=("missing",))
    with pytest.raises(ValueError):
        build_disaggregated_execution_plan(
            namespace_type=GlobalMemoryNamespace.PROJECT,
            namespace_id="p1",
            source_execution_graph_id="graph-1",
            segments=(bad,),
        )


def test_cycle_fails_closed():
    a = make_segment(sequence=1)
    b = make_segment(sequence=2, dependencies=(a.segment_id,))
    a2 = make_segment(
        sequence=1,
        segment_id=a.segment_id,
        dependencies=(b.segment_id,),
    )
    with pytest.raises(ValueError):
        build_disaggregated_execution_plan(
            namespace_type=GlobalMemoryNamespace.PROJECT,
            namespace_id="p1",
            source_execution_graph_id="graph-1",
            segments=(a2, b),
        )
