import pytest

from mercury.context_prediction.candidates import build_prediction_candidates
from mercury.global_memory.contracts import (
    GlobalMemoryConflictState,
    GlobalMemoryLifecycle,
    GlobalMemoryNamespace,
)
from tests._context_prediction_helpers import (
    global_record,
    request,
    scope,
    session_record,
    store,
)


def test_builds_deterministic_merged_candidate():
    session = session_record()
    global_source = global_record(
        conflict_state=GlobalMemoryConflictState.CONFLICTING,
    )
    first = build_prediction_candidates(
        request(),
        session_records=(session,),
        session_scope=scope(),
        global_store=store(global_source),
    )
    second = build_prediction_candidates(
        request(),
        session_records=(session,),
        session_scope=scope(),
        global_store=store(global_source),
    )
    assert first == second
    assert len(first) == 1
    assert first[0].source_global_record_ids == ("g1",)
    assert first[0].source_phase8_record_ids == ("s1",)
    assert first[0].conflict_present is True


def test_closed_namespace_fails_closed():
    closed = store().close_namespace(
        GlobalMemoryNamespace.PROJECT,
        "p1",
        closure_reason="project ended",
        closure_sequence=1,
    )
    with pytest.raises(ValueError, match="closed namespace"):
        build_prediction_candidates(request(), global_store=closed)


def test_cross_namespace_source_fails_closed():
    bad = global_record(namespace_id="other")
    with pytest.raises(ValueError, match="cross-namespace"):
        build_prediction_candidates(request(), global_store=store(bad))


@pytest.mark.parametrize(
    "lifecycle",
    (
        GlobalMemoryLifecycle.REVOKED,
        GlobalMemoryLifecycle.EXPIRED,
        GlobalMemoryLifecycle.SUPERSEDED,
        GlobalMemoryLifecycle.TOMBSTONED,
    ),
)
def test_non_active_sources_are_excluded(lifecycle):
    dead = global_record(lifecycle=lifecycle)
    assert build_prediction_candidates(
        request(),
        global_store=store(dead),
    ) == ()


def test_permutation_does_not_change_candidate_result():
    a = session_record("s2", "risk", creation_sequence=2)
    b = session_record("s1", "risk")
    assert build_prediction_candidates(
        request(),
        session_records=(a, b),
        session_scope=scope(),
    ) == build_prediction_candidates(
        request(),
        session_records=(b, a),
        session_scope=scope(),
    )


def test_candidate_cap_fails_closed():
    records = tuple(session_record(f"s{i}", f"k{i}") for i in range(257))
    with pytest.raises(ValueError, match="too many prediction candidates"):
        build_prediction_candidates(
            request(), session_records=records, session_scope=scope()
        )


def test_same_session_cannot_use_another_namespace_scope():
    with pytest.raises(ValueError, match="session namespace scope mismatch"):
        build_prediction_candidates(
            request(),
            session_records=(session_record(),),
            session_scope=scope(namespace_id="p2"),
        )


def test_another_session_cannot_use_authorized_namespace_scope():
    with pytest.raises(ValueError, match="session scope mismatch"):
        build_prediction_candidates(
            request(),
            session_records=(session_record(session_id="session-other"),),
            session_scope=scope(),
        )
