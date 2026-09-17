"""Deterministic, exact-namespace global context retrieval."""

from mercury.global_memory.contracts import (
    GlobalContextRecord,
    GlobalMemoryLifecycle,
    GlobalMemoryPhaseStatus,
    GlobalMemoryQuery,
    GlobalMemoryRetrievalResult,
)
from mercury.global_memory.store import GlobalContextStore


_DEFAULT_LIFECYCLES = frozenset((
    GlobalMemoryLifecycle.ACTIVE,
    GlobalMemoryLifecycle.SUPERSEDED,
))


def _matches(record: GlobalContextRecord, query: GlobalMemoryQuery) -> bool:
    if (record.namespace_type, record.namespace_id) != (query.namespace_type, query.namespace_id):
        return False
    if query.memory_types is not None and record.memory_type not in query.memory_types:
        return False
    if query.context_key is not None and record.context_key != query.context_key:
        return False
    if query.source_artifact_id is not None and query.source_artifact_id not in record.source_artifact_ids:
        return False
    if query.source_phase8_record_ids is not None and not set(query.source_phase8_record_ids).issubset(record.source_phase8_record_ids):
        return False
    if query.record_version is not None and record.record_version != query.record_version:
        return False
    if query.lifecycle is not None:
        if record.lifecycle is not query.lifecycle:
            return False
    elif record.lifecycle not in _DEFAULT_LIFECYCLES:
        return False
    if query.current_only and record.lifecycle is not GlobalMemoryLifecycle.ACTIVE:
        return False
    if query.conflict_state is not None and record.conflict_state is not query.conflict_state:
        return False
    return True


def retrieve_global_context(query: GlobalMemoryQuery, store: GlobalContextStore) -> GlobalMemoryRetrievalResult:
    """Return an exact-namespace, canonically ordered, bounded record tuple."""
    if not isinstance(query, GlobalMemoryQuery) or not isinstance(store, GlobalContextStore):
        raise ValueError("certified query and store required")
    if (query.namespace_type, query.namespace_id) != (
        query.authorized_namespace_type,
        query.authorized_namespace_id,
    ):
        raise ValueError("namespace authorization mismatch")
    if any(not isinstance(record, GlobalContextRecord) for record in store.records):
        raise ValueError("malformed stored record")
    records = sorted(
        (record for record in store.records if _matches(record, query)),
        key=lambda record: (
            record.namespace_type.value,
            record.namespace_id,
            record.context_key,
            record.record_version,
            record.creation_sequence,
            record.global_record_id,
        ),
    )
    return GlobalMemoryRetrievalResult(
        status=GlobalMemoryPhaseStatus.READY,
        records=tuple(records[:query.limit]),
    )
