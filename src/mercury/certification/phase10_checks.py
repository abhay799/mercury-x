"""Small executable certification probes for the Phase 10 public boundary.

These probes run production interfaces with immutable, local fixtures. They do
not run pytest, launch processes, write memory, or treat manifest text as proof.
Explicit exceptions keep every invariant active when Python runs with ``-O``.
"""

from pathlib import Path
import math

from mercury.context_prediction import candidates, contracts, features, integration, scoring
from mercury.global_memory.contracts import (
    GlobalContextRecord, GlobalMemoryConflictState, GlobalMemoryLifecycle,
    GlobalMemoryNamespace, GlobalMemoryType, global_context_record_id,
)
from mercury.global_memory.store import GlobalContextStore


class CertificationCheckFailure(ValueError):
    """An executable observation disagreed with the certified invariant."""


def _require(condition, reason):
    if not condition:
        raise CertificationCheckFailure(reason)


def _rejects(operation, reason):
    try:
        operation()
    except (ValueError, TypeError):
        return
    raise CertificationCheckFailure(reason)


def _request(**changes):
    payload = dict(
        namespace_type=GlobalMemoryNamespace.PROJECT,
        namespace_id="certification-project",
        authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
        authorized_namespace_id="certification-project",
        predictor_id="phase10-certification", predictor_version="1",
    )
    payload.update(changes)
    return contracts.ContextPredictionRequest(**payload)


def _record(*, key="context-a", **changes):
    payload = dict(
        namespace_type=GlobalMemoryNamespace.PROJECT,
        namespace_id="certification-project", global_record_id="pending",
        record_version=1, source_session_id="session-a",
        source_phase8_record_ids=("phase8-record-a",),
        source_artifact_ids=("artifact-a",), source_phase="8",
        memory_type=GlobalMemoryType.PROJECT_CONTEXT, context_key=key,
        creation_sequence=1, lifecycle=GlobalMemoryLifecycle.ACTIVE,
        conflict_state=GlobalMemoryConflictState.CLEAR,
        provenance=("Explicit certification source evidence.",),
        promotion_policy_id="explicit-promotion", retention_policy_id="bounded-retention",
    )
    payload.update(changes)
    draft = GlobalContextRecord(**payload)
    return draft.model_copy(update={"global_record_id": global_context_record_id(draft)})


def _store(*records):
    return GlobalContextStore(records=records or (_record(),))


def _candidates(*records, **kwargs):
    return candidates.build_prediction_candidates(_request(), global_store=_store(*records), **kwargs)


def _predict(*records, request=None, **kwargs):
    return integration.predict_context(request or _request(), global_store=_store(*records), **kwargs)


def _vector(value=0.0, **changes):
    payload = {
        name: value for name in (
            "recency", "task_continuity", "context_key_recurrence", "dependency_adjacency",
            "source_lineage_overlap", "artifact_continuity", "session_global_agreement",
            "lifecycle_eligibility", "conflict_state", "horizon_compatibility",
        )
    }
    payload.update(changes)
    return contracts.ContextPredictionFeatureVector(candidate_id="certification-vector", **payload)


def _request_rejects_fields(names):
    for name in names:
        _rejects(lambda: _request(**{name: "forbidden"}), f"Unsupported request field accepted: {name}")


def check_horizons():
    _require(tuple(item.value for item in contracts.ContextPredictionHorizon) == (
        "NEXT_TURN", "NEXT_TASK", "SESSION_NEAR_TERM",
    ), "Certified horizon vocabulary changed.")
    _rejects(lambda: contracts.ContextPredictionHorizon("LONG_TERM"), "Uncertified horizon accepted.")
    check_deterministic_horizon()


def check_confidence_bands():
    _require(tuple(item.value for item in contracts.ContextConfidenceBand) == (
        "LOW", "MEDIUM", "HIGH",
    ), "Certified confidence vocabulary changed.")
    check_deterministic_confidence_band()


def check_limits():
    _require((contracts.MAX_PREDICTION_CANDIDATES, contracts.MAX_CONTEXT_PREDICTIONS,
              contracts.MAX_SOURCE_RECORDS_PER_PREDICTION, contracts.MAX_REASON_CODES)
             == (256, 64, 128, 16), "Certified limits changed.")
    for limit in (0, -1, 65):
        _rejects(lambda: _request(limit=limit), "Invalid prediction limit accepted.")
    _require(_request().limit == 64, "Default limit changed.")


def check_candidate_identity():
    first, = _candidates()
    second, = _candidates()
    _require(first == second and len(first.candidate_id) == 64, "Candidate ID is not deterministic SHA-256.")
    _rejects(lambda: contracts.ContextPredictionCandidate.model_validate({
        **first.model_dump(), "candidate_id": "0" * 64,
    }), "Altered candidate digest accepted.")
    other, = _candidates(_record(record_version=2))
    _require(other.candidate_id != first.candidate_id, "Exact source version did not affect identity.")


def check_prediction_identity():
    first, = _predict().predictions
    second, = _predict().predictions
    _require(first == second and len(first.prediction_id) == 64, "Prediction ID is not deterministic SHA-256.")
    _rejects(lambda: contracts.ContextPrediction.model_validate({
        **first.model_dump(), "prediction_id": "0" * 64,
    }), "Altered prediction digest accepted.")


def check_namespace_authorization():
    _rejects(lambda: _request(authorized_namespace_id="another-project"), "Unauthorized request accepted.")
    forged = _request().model_copy(update={"authorized_namespace_id": "another-project"})
    _rejects(lambda: candidates.build_prediction_candidates(forged, global_store=_store()),
             "Forged request bypassed authorization revalidation.")


def check_namespace_isolation():
    foreign = _record(namespace_id="another-project", key="foreign")
    try:
        output = _candidates(_record(), foreign)
    except ValueError:
        return
    _require(len(output) == 1 and output[0].context_key == "context-a", "Foreign namespace leaked.")
    _require(foreign.global_record_id not in output[0].source_global_record_ids, "Foreign lineage leaked.")


def check_closed_namespace():
    store = _store().close_namespace(
        GlobalMemoryNamespace.PROJECT, "certification-project",
        closure_reason="Explicit closure for certification.", closure_sequence=2,
    )
    _rejects(lambda: candidates.build_prediction_candidates(_request(), global_store=store),
             "Closed namespace accepted by candidate builder.")


def check_lifecycle_eligibility():
    _require(len(_candidates()) == 1, "Active source lost.")
    for state in GlobalMemoryLifecycle:
        if state is not GlobalMemoryLifecycle.ACTIVE:
            _require(_candidates(_record(lifecycle=state)) == (), "Ineligible lifecycle produced candidates.")


def check_source_traceability():
    record = _record(record_version=3)
    candidate, = _candidates(record)
    prediction, = _predict(record).predictions
    for output in (candidate, prediction):
        _require(output.source_global_record_ids == (record.global_record_id,), "Global source identity lost.")
        _require(output.source_phase8_record_ids == ("phase8-record-a",), "Phase 8 lineage lost.")
        _require(len(output.source_evidence) == 1, "Source evidence missing.")
        evidence = output.source_evidence[0]
        _require(evidence.record_id == record.global_record_id and evidence.record_version == 3,
                 "Exact source identity/version lost.")
        _require(evidence.source_artifact_ids == ("artifact-a",) and evidence.provenance == record.provenance,
                 "Source artifact/provenance lost.")
        _require(evidence.creation_sequence == record.creation_sequence and bool(evidence.sequence_scope),
                 "Source sequence scope lost.")


def check_source_immutability():
    store = _store()
    request = _request()
    before = store.model_dump_json(), request.model_dump_json()
    result = integration.predict_context(request, global_store=store)
    _require(before == (store.model_dump_json(), request.model_dump_json()), "Input source mutated.")
    _rejects(lambda: setattr(result.predictions[0], "context_key", "changed"), "Prediction is mutable.")


def check_deterministic_features():
    candidate, = _candidates()
    first = features.extract_prediction_features(candidate, current_artifact_ids=("b", "artifact-a"))
    second = features.extract_prediction_features(candidate, current_artifact_ids=("artifact-a", "b"))
    _require(first == second, "Equivalent feature inputs diverge.")
    _require(first.session_global_agreement == 0.0, "Promoted lineage fabricated session/global agreement.")
    _require(first.recency is None, "Missing recency silently invented.")


def check_bounded_confidence():
    for value, expected in ((0.0, 0.0), (0.5, 0.5), (1.0, 1.0)):
        confidence = scoring.score_prediction(_vector(value))[1]
        _require(math.isfinite(confidence) and 0.0 <= confidence <= 1.0,
                 "Confidence is outside certified bounds.")
        _require(abs(confidence - expected) < 1e-10, "Weighted confidence disagrees with known fixture.")
    for value in (-0.1, 1.1, float("nan"), float("inf")):
        _rejects(lambda: _vector(value), "Invalid numeric feature accepted.")


def check_deterministic_confidence_band():
    for value, expected in ((0.0, "LOW"), (0.39, "LOW"), (0.40, "MEDIUM"),
                            (0.74, "MEDIUM"), (0.75, "HIGH"), (1.0, "HIGH")):
        output = scoring.score_prediction(_vector(value))
        _require(output[2].value == expected, "Confidence band threshold changed.")
        _require(output == scoring.score_prediction(_vector(value)), "Scoring is nondeterministic.")


def check_deterministic_horizon():
    cases = (
        ({}, "SESSION_NEAR_TERM"),
        ({"task_continuity": 0.75}, "NEXT_TURN"),
        ({"dependency_adjacency": 0.75}, "NEXT_TASK"),
        ({"source_lineage_overlap": 0.75}, "NEXT_TASK"),
        ({"task_continuity": 1.0, "dependency_adjacency": 1.0}, "NEXT_TURN"),
    )
    for fields, expected in cases:
        _require(scoring.score_prediction(_vector(**fields))[0].value == expected,
                 "Deterministic horizon rule changed.")


def check_reason_codes():
    ordinary = scoring.score_prediction(_vector(conflict_state=1.0))[3]
    _require(tuple(item.value for item in ordinary) == ("NEAR_TERM_SESSION_SIGNAL",),
             "Unsupported or missing baseline reason.")
    reasons = scoring.score_prediction(_vector(1.0, conflict_state=0.0))[3]
    _require(tuple(item.value for item in reasons) == (
        "ARTIFACT_CONTINUITY", "CONFLICT_PRESENT", "CONTEXT_RECURRENCE", "DEPENDENCY_ADJACENCY",
        "SESSION_GLOBAL_AGREEMENT", "SOURCE_LINEAGE_OVERLAP", "TASK_CONTINUITY",
    ), "Evidence reasons are missing or noncanonical.")


def check_conflict_preservation():
    record = _record(conflict_state=GlobalMemoryConflictState.CONFLICTING)
    candidate, = _candidates(record)
    prediction, = _predict(record).predictions
    _require(candidate.conflict_present, "Conflict erased in candidate.")
    _require(contracts.ContextPredictionReasonCode.CONFLICT_PRESENT in prediction.reason_codes,
             "Conflict reason erased.")
    _require(prediction.source_evidence[0].conflict_state is GlobalMemoryConflictState.CONFLICTING,
             "Source conflict metadata erased.")
    clear, = _predict(_record()).predictions
    _require(prediction.confidence < clear.confidence, "Conflict did not reduce confidence.")


def check_prediction_ordering():
    a, b, c = _record(key="a"), _record(key="b"), _record(key="c")
    options = dict(current_context_key="b", dependency_context_keys=("c",))
    first = _predict(a, b, c, **options)
    second = _predict(c, a, b, **options)
    _require(first == second, "Source ordering changes predictions.")
    _require(tuple(item.context_key for item in first.predictions) == ("b", "c", "a"),
             "Predictions do not follow certified horizon order.")


def check_prediction_limit():
    records = tuple(_record(key=f"context-{index:03d}") for index in range(65))
    _require(len(_predict(*records).predictions) == 64, "Default prediction cap not enforced.")
    limited = _predict(*records, request=_request(limit=3))
    _require(len(limited.predictions) == 3, "Caller prediction cap not enforced.")
    _require(tuple(item.context_key for item in limited.predictions)
             == ("context-000", "context-001", "context-002"), "Cap does not preserve canonical ordering.")


def check_source_limit():
    records = tuple(_record(record_version=index + 1) for index in range(129))
    _rejects(lambda: _candidates(*records), "Source cap was bypassed.")
    _require(len(_candidates(records[0])) == 1, "Valid bounded source rejected.")


def check_no_semantic_ranking():
    _request_rejects_fields(("embedding", "vector_query", "semantic_query", "relevance_score", "selected_model"))
    candidate, = _candidates(_record(key="same phrase"))
    vector = features.extract_prediction_features(candidate, current_context_key="Same phrase")
    _require(vector.task_continuity == 0.0, "Context matching used fuzzy/semantic inference.")


def check_no_memory_persistence():
    store = _store()
    before = store.model_dump_json(), store.fingerprint
    integration.predict_context(_request(), global_store=store)
    _require(before == (store.model_dump_json(), store.fingerprint), "Prediction persisted or modified memory.")
    _request_rejects_fields(("persist", "promotion_policy", "write_memory"))


def check_no_prefetch_cache():
    _request_rejects_fields(("prefetch", "cache", "cache_key", "cache_warming"))
    output = _predict()
    _require(not ({"prefetch", "cache", "cache_key", "cache_warming"} & set(type(output).model_fields)),
             "Prediction output exposes cache actions.")


def check_no_execution_control():
    fields = ("scheduler", "runtime", "device", "hardware", "placement", "selected_model", "execute")
    _request_rejects_fields(fields)
    output, = _predict().predictions
    _require(not (set(fields) & set(type(output).model_fields)), "Prediction exposes execution control.")


def check_no_user_profile_prediction():
    for namespace in ("USER_PROFILE", "CROSS_SESSION", "GLOBAL"):
        _rejects(lambda: _request(namespace_type=namespace, authorized_namespace_type=namespace),
                 "Uncertified profile namespace accepted.")
    _request_rejects_fields(("user_profile", "personality", "behavior_profile"))


def check_adversarial_integration():
    _rejects(lambda: candidates.build_prediction_candidates(_request(), global_store={"records": []}),
             "Untyped store accepted.")
    malformed = _record().model_copy(update={"record_version": 0})
    _rejects(lambda: _candidates(malformed), "Malformed source version accepted.")
    _rejects(lambda: candidates.build_prediction_candidates(_request(), session_records=({"record_id": "spoof"},)),
             "Untyped session source accepted.")
    first = _predict(_record(), current_context_key="context-a")
    _require(first == _predict(_record(), current_context_key="context-a"), "End-to-end output is nondeterministic.")


def run_check(gate_id):
    from mercury.certification.phase10 import REQUIRED_PHASE10_GATE_IDS

    if gate_id not in REQUIRED_PHASE10_GATE_IDS:
        raise ValueError("unknown executable gate")
    root = Path(__file__).parents[1] / "context_prediction"
    for name in ("contracts.py", "candidates.py", "features.py", "scoring.py", "predictor.py", "integration.py"):
        _require((root / name).is_file(), f"Required source artifact missing: {name}")
    globals()[f"check_{gate_id}"]()
