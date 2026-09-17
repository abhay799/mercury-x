from dataclasses import dataclass

import pytest

from mercury.context_prediction.candidates import build_prediction_candidates
from mercury.context_prediction.contracts import ContextPredictionRequest
from mercury.global_memory.contracts import (
    GlobalMemoryConflictState,
    GlobalMemoryNamespace,
)


@dataclass(frozen=True)
class Record:
    record_id: str
    context_key: str
    lifecycle: str = "ACTIVE"
    namespace_type: object | None = None
    namespace_id: str | None = None
    creation_sequence: int = 1
    source_artifact_ids: tuple[str, ...] = ()
    source_phase8_record_ids: tuple[str, ...] = ()
    conflict_state: object = GlobalMemoryConflictState.CLEAR


class Store:
    def __init__(self, records=(), closed=False):
        self.records = tuple(records)
        self.closed = closed

    def is_namespace_closed(self, namespace_type, namespace_id):
        return self.closed


def request():
    return ContextPredictionRequest(
        namespace_type=GlobalMemoryNamespace.PROJECT,
        namespace_id="p1",
        authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
        authorized_namespace_id="p1",
        predictor_id="phase10",
        predictor_version="1",
    )


def test_builds_deterministic_merged_candidate():
    session = Record(
        "s1",
        "risk",
        namespace_type=GlobalMemoryNamespace.PROJECT,
        namespace_id="p1",
        source_artifact_ids=("a1",),
    )
    global_record = Record(
        "g1",
        "risk",
        namespace_type=GlobalMemoryNamespace.PROJECT,
        namespace_id="p1",
        source_phase8_record_ids=("s1",),
        conflict_state=GlobalMemoryConflictState.CONFLICTING,
    )
    first = build_prediction_candidates(
        request(),
        session_records=(session,),
        global_store=Store((global_record,)),
    )
    second = build_prediction_candidates(
        request(),
        session_records=(session,),
        global_store=Store((global_record,)),
    )
    assert first == second
    assert len(first) == 1
    assert first[0].source_global_record_ids == ("g1",)
    assert first[0].source_phase8_record_ids == ("s1",)
    assert first[0].conflict_present is True


def test_closed_namespace_fails_closed():
    with pytest.raises(ValueError):
        build_prediction_candidates(request(), global_store=Store(closed=True))


def test_cross_namespace_source_fails_closed():
    bad = Record(
        "s1",
        "risk",
        namespace_type=GlobalMemoryNamespace.PROJECT,
        namespace_id="other",
    )
    with pytest.raises(ValueError):
        build_prediction_candidates(request(), session_records=(bad,))


def test_non_active_sources_are_excluded():
    dead = Record(
        "g1",
        "risk",
        lifecycle="REVOKED",
        namespace_type=GlobalMemoryNamespace.PROJECT,
        namespace_id="p1",
    )
    assert build_prediction_candidates(
        request(),
        global_store=Store((dead,)),
    ) == ()


def test_permutation_does_not_change_candidate_result():
    a = Record("s2", "risk")
    b = Record("s1", "risk")
    assert build_prediction_candidates(
        request(),
        session_records=(a, b),
    ) == build_prediction_candidates(
        request(),
        session_records=(b, a),
    )


def test_candidate_cap_fails_closed():
    records = tuple(Record(f"s{i}", f"k{i}") for i in range(257))
    with pytest.raises(ValueError):
        build_prediction_candidates(request(), session_records=records)
