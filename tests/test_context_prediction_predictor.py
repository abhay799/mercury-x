from mercury.context_prediction.contracts import (
    ContextPredictionCandidate,
    ContextPredictionFeatureVector,
    ContextPredictionRequest,
    GlobalMemoryNamespace,
    make_context_prediction_candidate_id,
)
from mercury.context_prediction.predictor import assemble_context_predictions


def request(limit=64):
    return ContextPredictionRequest(
        namespace_type=GlobalMemoryNamespace.PROJECT,
        namespace_id="p1",
        authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
        authorized_namespace_id="p1",
        predictor_id="phase10",
        predictor_version="1",
        limit=limit,
    )


def candidate(key, sequence=1):
    cid = make_context_prediction_candidate_id(
        namespace_type=GlobalMemoryNamespace.PROJECT,
        namespace_id="p1",
        context_key=key,
        source_global_record_ids=(f"g-{key}",),
        source_phase8_record_ids=(),
        source_artifact_ids=(),
        conflict_present=False,
        creation_sequence=sequence,
    )
    return ContextPredictionCandidate(
        namespace_type=GlobalMemoryNamespace.PROJECT,
        namespace_id="p1",
        context_key=key,
        candidate_id=cid,
        source_global_record_ids=(f"g-{key}",),
        source_phase8_record_ids=(),
        source_artifact_ids=(),
        conflict_present=False,
        creation_sequence=sequence,
    )


def features(c, continuity=0.0, dependency=0.0):
    return ContextPredictionFeatureVector(
        candidate_id=c.candidate_id,
        recency=0.5,
        task_continuity=continuity,
        context_key_recurrence=0.0,
        dependency_adjacency=dependency,
        source_lineage_overlap=0.0,
        artifact_continuity=0.0,
        session_global_agreement=0.0,
        lifecycle_eligibility=1.0,
        conflict_state=1.0,
        horizon_compatibility=1.0 if continuity else 0.25,
    )


def test_assembly_is_deterministic_and_canonically_ordered():
    a = candidate("a")
    b = candidate("b")
    first = assemble_context_predictions(
        request(),
        (b, a),
        (features(b, dependency=1.0), features(a, continuity=1.0)),
    )
    second = assemble_context_predictions(
        request(),
        (a, b),
        (features(a, continuity=1.0), features(b, dependency=1.0)),
    )
    assert first == second
    assert first.predictions[0].context_key == "a"


def test_request_limit_bounds_result():
    candidates = tuple(candidate(f"k{i}") for i in range(3))
    vectors = tuple(features(c) for c in candidates)
    result = assemble_context_predictions(request(limit=2), candidates, vectors)
    assert len(result.predictions) == 2
