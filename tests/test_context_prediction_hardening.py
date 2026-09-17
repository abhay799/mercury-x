from types import SimpleNamespace

import pytest

from mercury.context_prediction.candidates import build_prediction_candidates
from mercury.context_prediction.integration import predict_context
from mercury.context_prediction.features import extract_prediction_features
from mercury.context_prediction.scoring import score_prediction
from mercury.global_memory.contracts import GlobalMemoryNamespace, GlobalMemoryLifecycle, GlobalMemoryConflictState
from mercury.session_memory.contracts import SessionMemoryLifecycle
from tests._context_prediction_helpers import request, scope, session_record, global_record, store


def test_real_phase8_retrieval_key_requires_explicit_namespace_session_binding():
    source = session_record()
    with pytest.raises(ValueError, match="scope"):
        build_prediction_candidates(request(), session_records=(source,))
    candidates = build_prediction_candidates(request(), session_records=(source,), session_scope=scope())
    assert candidates[0].context_key == "risk"
    assert candidates[0].source_phase8_record_ids == ("s1",)
    assert candidates[0].source_evidence[0].provenance == ("session-proof",)


def test_global_provenance_and_conflict_preserved_through_prediction():
    sources = (global_record(), global_record("g2", conflict_state=GlobalMemoryConflictState.CONFLICTING,
                                             provenance=("contradictory-proof",)))
    result = predict_context(request(), global_store=store(*sources))
    prediction = result.predictions[0]
    assert prediction.source_global_record_ids == ("g1", "g2")
    assert [item.provenance for item in prediction.source_evidence] == [("global-proof",), ("contradictory-proof",)]
    assert prediction.source_evidence[1].conflict_state is GlobalMemoryConflictState.CONFLICTING
    assert "CONFLICT_PRESENT" in prediction.reason_codes


@pytest.mark.parametrize("source", [dict(record_id="s1", context_key="risk"), SimpleNamespace(record_id="s1", context_key="risk")])
def test_unsupported_duck_typed_sources_rejected(source):
    with pytest.raises(ValueError):
        build_prediction_candidates(request(), session_records=(source,))


@pytest.mark.parametrize("field", ["lifecycle", "namespace_type", "namespace_id", "provenance", "creation_sequence"])
def test_constructed_global_with_missing_required_field_rejected(field):
    data = global_record().model_dump()
    data.pop(field)
    malformed = type(global_record()).model_construct(**data)
    with pytest.raises(ValueError):
        build_prediction_candidates(request(), global_store=store(malformed))


@pytest.mark.parametrize("provenance", [(), ("",), (" ",)])
def test_missing_or_blank_global_provenance_rejected(provenance):
    with pytest.raises(ValueError):
        predict_context(request(), global_store=store(global_record(provenance=provenance)))


@pytest.mark.parametrize("namespace", list(GlobalMemoryNamespace))
def test_namespace_isolation_and_closed_namespace(namespace):
    req = request(namespace_type=namespace, authorized_namespace_type=namespace)
    with pytest.raises(ValueError):
        predict_context(req, global_store=store(global_record(namespace_type=namespace, namespace_id="other")))
    closed = store().close_namespace(namespace, "p1", closure_reason="closed", closure_sequence=1)
    with pytest.raises(ValueError):
        predict_context(req, global_store=closed)


@pytest.mark.parametrize("lifecycle", [value for value in GlobalMemoryLifecycle if value is not GlobalMemoryLifecycle.ACTIVE])
def test_inactive_global_evidence_is_excluded(lifecycle):
    assert predict_context(request(), global_store=store(global_record(lifecycle=lifecycle))).predictions == ()


@pytest.mark.parametrize("lifecycle", [value for value in SessionMemoryLifecycle if value is not SessionMemoryLifecycle.ACTIVE])
def test_inactive_session_evidence_is_excluded(lifecycle):
    assert predict_context(request(), session_records=(session_record(lifecycle=lifecycle),), session_scope=scope()).predictions == ()


def test_duplicates_cannot_hide_conflicting_source_identity():
    first = global_record()
    conflicting = first.model_copy(update={"provenance": ("different-proof",)})
    with pytest.raises(ValueError, match="duplicate"):
        predict_context(request(), global_store=store(first, conflicting))


def test_identical_duplicates_and_source_permutations_preserve_result_and_input():
    a, b = global_record(), global_record("g2", creation_sequence=2)
    original = store(a, b)
    before = original.model_dump_json()
    once = predict_context(request(), global_store=original)
    repeated = predict_context(request(), global_store=store(b, a, a))
    assert once == repeated
    assert original.model_dump_json() == before


def test_generator_hints_are_not_consumed_per_candidate():
    records = store(global_record("g1", "a"), global_record("g2", "b"))
    supplied = dict(dependency_context_keys=("a", "b"), current_artifact_ids=("a1",),
                    current_phase8_record_ids=("s1",), recent_context_keys=("a", "b"))
    expected = predict_context(request(), global_store=records, **supplied)
    actual = predict_context(request(), global_store=records, **{k: iter(v) for k, v in supplied.items()})
    assert actual == expected


def test_recency_uses_exact_sequence_reference_and_not_wall_clock():
    candidates = build_prediction_candidates(request(), global_store=store(
        global_record("g1", "old", creation_sequence=2), global_record("g2", "new", creation_sequence=5)))
    by_key = {c.context_key: c for c in candidates}
    refs = {("GLOBAL", "p1"): 5}
    old = extract_prediction_features(by_key["old"], reference_sequences=refs)
    new = extract_prediction_features(by_key["new"], reference_sequences=refs)
    assert old.recency == 0.25  # 1 / (1 + (5 - 2))
    assert new.recency == 1.0
    assert score_prediction(new)[1] - score_prediction(old)[1] == pytest.approx(0.075)


def test_recency_without_reference_is_explicitly_unavailable_and_adds_no_score():
    candidate = build_prediction_candidates(request(), global_store=store(global_record()))[0]
    features = extract_prediction_features(candidate)
    assert features.recency is None
    assert score_prediction(features)[1] == 0.1125
    with pytest.raises(ValueError):
        extract_prediction_features(candidate, reference_sequences={("GLOBAL", "p1"): 0})


def test_reference_before_source_fails_and_partial_domains_do_not_invent_age():
    candidate = build_prediction_candidates(request(), global_store=store(global_record(creation_sequence=5)),
                                            session_records=(session_record(creation_sequence=500),), session_scope=scope())[0]
    with pytest.raises(ValueError):
        extract_prediction_features(candidate, reference_sequences={("GLOBAL", "p1"): 4})
    assert extract_prediction_features(candidate, reference_sequences={("GLOBAL", "p1"): 5}).recency is None
    assert extract_prediction_features(candidate, reference_sequences={("GLOBAL", "p1"): 5, ("SESSION", "session-1"): 501}).recency == 0.75


def test_global_lineage_alone_does_not_claim_session_global_agreement():
    candidate = build_prediction_candidates(request(), global_store=store(global_record()))[0]
    assert extract_prediction_features(candidate).session_global_agreement == 0.0


def test_real_independent_session_and_global_observation_can_agree():
    candidate = build_prediction_candidates(request(), global_store=store(global_record()),
                                            session_records=(session_record(),), session_scope=scope())[0]
    assert extract_prediction_features(candidate).session_global_agreement == 1.0


def test_legacy_candidate_without_evidence_has_no_invented_recency():
    from tests.test_context_prediction_predictor import candidate
    assert extract_prediction_features(candidate("old")).recency is None
