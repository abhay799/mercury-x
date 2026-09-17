"""Typed, exact-scope adapters for already-authorized Phase 8/9 sources."""
from collections import defaultdict
from collections.abc import Iterable

from mercury.context_prediction.contracts import (
    MAX_PREDICTION_CANDIDATES, MAX_SOURCE_RECORDS_PER_PREDICTION,
    ContextPredictionCandidate, ContextPredictionRequest, ContextPredictionSourceEvidence,
    SessionPredictionScope, make_context_prediction_candidate_id,
)
from mercury.global_memory.contracts import GlobalContextRecord, GlobalMemoryLifecycle, GlobalMemoryConflictState
from mercury.global_memory.store import GlobalContextStore
from mercury.session_memory.contracts import SessionMemoryRecord, SessionMemoryLifecycle


def _record(record, expected_type):
    if type(record) is not expected_type:
        raise ValueError(f"exact {expected_type.__name__} source required")
    # Copies and model_construct bypass frozen-model validation.
    data = record.model_dump()
    for name, field in expected_type.model_fields.items():
        if field.is_required() and name not in record.model_fields_set:
            raise ValueError(f"missing explicit source {name}")
    return expected_type.model_validate(data)


def _session_source(record: SessionMemoryRecord, scope: SessionPredictionScope):
    record = _record(record, SessionMemoryRecord)
    if record.schema_version != "mercury.session-memory/v1":
        raise ValueError("unsupported session source schema")
    if record.session_id != scope.session_id:
        raise ValueError("session scope mismatch")
    if not isinstance(record.retrieval_key, str) or not record.retrieval_key.strip():
        raise ValueError("explicit session retrieval_key required")
    evidence = ContextPredictionSourceEvidence(
        source_kind="SESSION", record_id=record.record_id, record_version=record.record_version,
        sequence_scope=record.session_id, creation_sequence=record.creation_sequence,
        source_artifact_ids=(record.source_artifact_id,), provenance=record.provenance,
    )
    return record, record.retrieval_key, evidence, record.lifecycle is SessionMemoryLifecycle.ACTIVE


def _global_source(record: GlobalContextRecord, request: ContextPredictionRequest):
    record = _record(record, GlobalContextRecord)
    if (record.namespace_type, record.namespace_id) != (request.namespace_type, request.namespace_id):
        raise ValueError("cross-namespace source forbidden")
    evidence = ContextPredictionSourceEvidence(
        source_kind="GLOBAL", record_id=record.global_record_id, record_version=record.record_version,
        sequence_scope=record.namespace_id, creation_sequence=record.creation_sequence,
        source_artifact_ids=record.source_artifact_ids, source_phase8_record_ids=record.source_phase8_record_ids,
        provenance=record.provenance, conflict_state=record.conflict_state,
    )
    return record, record.context_key, evidence, record.lifecycle is GlobalMemoryLifecycle.ACTIVE


def build_prediction_candidates(
    request: ContextPredictionRequest,
    *,
    session_records: Iterable[SessionMemoryRecord] = (),
    global_store: GlobalContextStore | None = None,
    session_scope: SessionPredictionScope | None = None,
    dependency_context_keys: Iterable[str] = (),
) -> tuple[ContextPredictionCandidate, ...]:
    if type(request) is not ContextPredictionRequest:
        raise ValueError("context prediction request required")
    request = ContextPredictionRequest.model_validate(request.model_dump())
    if any(not isinstance(key, str) or not key.strip() for key in dependency_context_keys):
        raise ValueError("dependency context key must be nonblank")
    if session_scope is not None:
        if type(session_scope) is not SessionPredictionScope:
            raise ValueError("explicit session scope required")
        session_scope = SessionPredictionScope.model_validate(session_scope.model_dump())
        if (session_scope.namespace_type, session_scope.namespace_id) != (request.namespace_type, request.namespace_id):
            raise ValueError("session namespace scope mismatch")
    sessions = tuple(session_records)
    if sessions and session_scope is None:
        raise ValueError("explicit session scope required")
    globals_ = ()
    if global_store is not None:
        if type(global_store) is not GlobalContextStore:
            raise ValueError("certified GlobalContextStore required")
        checked_store = GlobalContextStore.model_validate(global_store.model_dump())
        for closure in checked_store.closed_namespaces:
            if not closure.namespace_id.strip() or not closure.closure_reason.strip() or closure.closed is not True or closure.closure_sequence < 1:
                raise ValueError("malformed namespace closure")
        if checked_store.is_namespace_closed(request.namespace_type, request.namespace_id):
            raise ValueError("closed namespace cannot produce predictions")
        globals_ = global_store.records

    grouped = defaultdict(list)
    identities = {}
    for records, adapter in (
        (sessions, lambda source: _session_source(source, session_scope)),
        (globals_, lambda source: _global_source(source, request)),
    ):
        for source in records:
            record, key, evidence, active = adapter(source)
            identity = (evidence.source_kind, evidence.record_id)
            canonical = record.model_dump()
            for field in ("provenance", "source_phase8_record_ids", "source_artifact_ids"):
                if field in canonical:
                    canonical[field] = tuple(sorted(set(canonical[field])))
            if identity in identities:
                if identities[identity] != canonical:
                    raise ValueError("conflicting duplicate source identity")
                continue
            identities[identity] = canonical
            if active:
                grouped[key].append(evidence)
                if len(grouped) > MAX_PREDICTION_CANDIDATES:
                    raise ValueError("too many prediction candidates")

    candidates = []
    for key, sources in sorted(grouped.items()):
        global_ids = tuple(sorted(item.record_id for item in sources if item.source_kind == "GLOBAL"))
        phase8_ids = {item.record_id for item in sources if item.source_kind == "SESSION"}
        phase8_ids.update(rid for item in sources for rid in item.source_phase8_record_ids)
        phase8_ids = tuple(sorted(phase8_ids))
        if len(global_ids) + len(phase8_ids) > MAX_SOURCE_RECORDS_PER_PREDICTION:
            raise ValueError("too many source records for prediction candidate")
        data = dict(namespace_type=request.namespace_type, namespace_id=request.namespace_id,
                    context_key=key, source_global_record_ids=global_ids, source_phase8_record_ids=phase8_ids,
                    source_artifact_ids=tuple(sorted({aid for item in sources for aid in item.source_artifact_ids})),
                    conflict_present=any(item.conflict_state is GlobalMemoryConflictState.CONFLICTING for item in sources),
                    creation_sequence=max(item.creation_sequence for item in sources))
        candidates.append(ContextPredictionCandidate(
            candidate_id=make_context_prediction_candidate_id(**data), source_evidence=tuple(sources), **data))
    return tuple(candidates)
