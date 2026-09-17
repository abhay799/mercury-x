from collections import defaultdict
from collections.abc import Iterable
from typing import Any

from mercury.context_prediction.contracts import (
    MAX_PREDICTION_CANDIDATES,
    MAX_SOURCE_RECORDS_PER_PREDICTION,
    ContextPredictionCandidate,
    ContextPredictionRequest,
    make_context_prediction_candidate_id,
)
from mercury.global_memory.contracts import GlobalMemoryConflictState


def _value(obj: Any, *names: str, default=None):
    if isinstance(obj, dict):
        for name in names:
            if name in obj:
                return obj[name]
        return default
    for name in names:
        if hasattr(obj, name):
            return getattr(obj, name)
    if hasattr(obj, "model_dump"):
        data = obj.model_dump()
        for name in names:
            if name in data:
                return data[name]
    return default


def _enum_value(value):
    return getattr(value, "value", value)


def _text(value, *, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be nonblank")
    return value


def _text_tuple(value) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        value = (value,)
    result = tuple(str(item) for item in value)
    if any(not item.strip() for item in result):
        raise ValueError("source identity must be nonblank")
    return tuple(sorted(set(result)))


def _record_id(record: Any, *, global_record: bool) -> str:
    names = (
        ("global_record_id", "record_id", "memory_record_id", "memory_id", "id")
        if global_record
        else (
            "session_memory_record_id",
            "session_record_id",
            "record_id",
            "memory_record_id",
            "memory_id",
            "id",
        )
    )
    return _text(_value(record, *names), field_name="source record id")


def _context_key(record: Any) -> str:
    return _text(
        _value(record, "context_key", "memory_key", "key"),
        field_name="context_key",
    )


def _artifact_ids(record: Any) -> tuple[str, ...]:
    values = _value(
        record,
        "source_artifact_ids",
        "artifact_ids",
        default=None,
    )
    if values is None:
        single = _value(record, "source_artifact_id", "artifact_id", default=None)
        values = () if single is None else (single,)
    return _text_tuple(values)


def _phase8_ids_from_global(record: Any) -> tuple[str, ...]:
    values = _value(
        record,
        "source_phase8_record_ids",
        "source_session_memory_record_ids",
        default=None,
    )
    if values is None:
        single = _value(
            record,
            "source_phase8_record_id",
            "source_session_memory_record_id",
            default=None,
        )
        values = () if single is None else (single,)
    return _text_tuple(values)


def _validate_optional_namespace(record: Any, request: ContextPredictionRequest) -> None:
    namespace_type = _value(record, "namespace_type", default=None)
    namespace_id = _value(record, "namespace_id", default=None)

    if namespace_type is None and namespace_id is None:
        return
    if namespace_type is None or namespace_id is None:
        raise ValueError("partial namespace identity is forbidden")
    if (
        _enum_value(namespace_type) != request.namespace_type.value
        or namespace_id != request.namespace_id
    ):
        raise ValueError("cross-namespace source forbidden")


def _is_active(record: Any) -> bool:
    lifecycle = _value(record, "lifecycle", default="ACTIVE")
    return _enum_value(lifecycle) == "ACTIVE"


def _has_conflict(record: Any) -> bool:
    value = _value(record, "conflict_state", default=None)
    if value is None:
        return bool(_value(record, "conflict_present", default=False))
    return _enum_value(value) == GlobalMemoryConflictState.CONFLICTING.value


def _global_records(store: Any) -> tuple[Any, ...]:
    if store is None:
        return ()
    records = _value(store, "records", default=())
    return tuple(records)


def _namespace_closed(store: Any, request: ContextPredictionRequest) -> bool:
    if store is None:
        return False
    method = getattr(store, "is_namespace_closed", None)
    if method is None:
        return False
    return bool(method(request.namespace_type, request.namespace_id))


def build_prediction_candidates(
    request: ContextPredictionRequest,
    *,
    session_records: Iterable[Any] = (),
    global_store: Any | None = None,
    dependency_context_keys: Iterable[str] = (),
) -> tuple[ContextPredictionCandidate, ...]:
    if not isinstance(request, ContextPredictionRequest):
        raise ValueError("context prediction request required")

    if _namespace_closed(global_store, request):
        raise ValueError("closed namespace cannot produce predictions")

    dependency_keys = tuple(sorted(set(str(x) for x in dependency_context_keys)))
    if any(not key.strip() for key in dependency_keys):
        raise ValueError("dependency context key must be nonblank")

    grouped: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "global_ids": set(),
            "phase8_ids": set(),
            "artifact_ids": set(),
            "conflict": False,
            "sequences": [],
        }
    )

    for record in tuple(session_records):
        _validate_optional_namespace(record, request)
        if not _is_active(record):
            continue
        key = _context_key(record)
        rid = _record_id(record, global_record=False)
        entry = grouped[key]
        entry["phase8_ids"].add(rid)
        entry["artifact_ids"].update(_artifact_ids(record))
        sequence = _value(record, "creation_sequence", "sequence", default=1)
        if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 1:
            raise ValueError("invalid creation sequence")
        entry["sequences"].append(sequence)

    for record in _global_records(global_store):
        _validate_optional_namespace(record, request)
        if not _is_active(record):
            continue
        key = _context_key(record)
        rid = _record_id(record, global_record=True)
        entry = grouped[key]
        entry["global_ids"].add(rid)
        entry["phase8_ids"].update(_phase8_ids_from_global(record))
        entry["artifact_ids"].update(_artifact_ids(record))
        entry["conflict"] = entry["conflict"] or _has_conflict(record)
        sequence = _value(record, "creation_sequence", "sequence", default=1)
        if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 1:
            raise ValueError("invalid creation sequence")
        entry["sequences"].append(sequence)

    candidates = []
    for key in sorted(grouped):
        entry = grouped[key]
        global_ids = tuple(sorted(entry["global_ids"]))
        phase8_ids = tuple(sorted(entry["phase8_ids"]))
        artifact_ids = tuple(sorted(entry["artifact_ids"]))
        source_count = len(global_ids) + len(phase8_ids)
        if source_count == 0:
            raise ValueError("candidate must have source lineage")
        if source_count > MAX_SOURCE_RECORDS_PER_PREDICTION:
            raise ValueError("too many source records for prediction candidate")
        creation_sequence = max(entry["sequences"]) if entry["sequences"] else 1
        candidate_id = make_context_prediction_candidate_id(
            namespace_type=request.namespace_type,
            namespace_id=request.namespace_id,
            context_key=key,
            source_global_record_ids=global_ids,
            source_phase8_record_ids=phase8_ids,
            source_artifact_ids=artifact_ids,
            conflict_present=bool(entry["conflict"]),
            creation_sequence=creation_sequence,
        )
        candidates.append(
            ContextPredictionCandidate(
                namespace_type=request.namespace_type,
                namespace_id=request.namespace_id,
                context_key=key,
                candidate_id=candidate_id,
                source_global_record_ids=global_ids,
                source_phase8_record_ids=phase8_ids,
                source_artifact_ids=artifact_ids,
                conflict_present=bool(entry["conflict"]),
                creation_sequence=creation_sequence,
            )
        )

    if len(candidates) > MAX_PREDICTION_CANDIDATES:
        raise ValueError("too many prediction candidates")

    return tuple(
        sorted(
            candidates,
            key=lambda item: (
                item.namespace_type.value,
                item.namespace_id,
                item.context_key,
                item.candidate_id,
            ),
        )
    )
