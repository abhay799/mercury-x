import pytest

from mercury.context_prediction.contracts import (
    ContextPredictionCandidate,
    GlobalMemoryNamespace,
    make_context_prediction_candidate_id,
)
from mercury.context_prediction.features import extract_prediction_features


def candidate(conflict=False):
    gid = ("g1",)
    sid = ("s1",)
    aid = ("a1",)
    cid = make_context_prediction_candidate_id(
        namespace_type=GlobalMemoryNamespace.PROJECT,
        namespace_id="p1",
        context_key="risk",
        source_global_record_ids=gid,
        source_phase8_record_ids=sid,
        source_artifact_ids=aid,
        conflict_present=conflict,
        creation_sequence=1,
    )
    return ContextPredictionCandidate(
        namespace_type=GlobalMemoryNamespace.PROJECT,
        namespace_id="p1",
        context_key="risk",
        candidate_id=cid,
        source_global_record_ids=gid,
        source_phase8_record_ids=sid,
        source_artifact_ids=aid,
        conflict_present=conflict,
        creation_sequence=1,
    )


def test_features_are_deterministic_and_explainable():
    c = candidate()
    a = extract_prediction_features(
        c,
        current_context_key="risk",
        recent_context_keys=("risk", "x"),
        dependency_context_keys=("risk",),
        current_artifact_ids=("a1",),
        current_phase8_record_ids=("s1",),
    )
    b = extract_prediction_features(
        c,
        current_context_key="risk",
        recent_context_keys=("x", "risk"),
        dependency_context_keys=("risk",),
        current_artifact_ids=("a1",),
        current_phase8_record_ids=("s1",),
    )
    assert a == b
    assert a.task_continuity == 1.0
    assert a.dependency_adjacency == 1.0
    assert a.source_lineage_overlap == 1.0
    assert a.artifact_continuity == 1.0
    # Source lineage on a global candidate does not establish a contemporaneous
    # session observation. Agreement requires explicit SESSION and GLOBAL evidence.
    assert a.session_global_agreement == 0.0


def test_conflict_is_represented_not_resolved():
    assert extract_prediction_features(candidate(True)).conflict_state == 0.0


def test_frequency_alone_does_not_force_high_feature_total():
    features = extract_prediction_features(
        candidate(),
        recent_context_keys=("risk",) * 20,
    )
    assert features.context_key_recurrence == 1.0
    assert features.task_continuity == 0.0
    assert features.dependency_adjacency == 0.0


def test_bad_task_metadata_fails_closed():
    with pytest.raises(ValueError):
        extract_prediction_features(candidate(), current_context_key="")
