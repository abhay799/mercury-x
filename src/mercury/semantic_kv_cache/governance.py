import hashlib
import json

from mercury.global_memory.contracts import GlobalMemoryNamespace
from mercury.semantic_kv_cache.contracts import (
    SemanticKVCacheEntry,
    SemanticKVCacheState,
    make_semantic_kv_cache_entry_id,
)


def _transition(
    entry: SemanticKVCacheEntry,
    *,
    target_state: SemanticKVCacheState,
    reason: str | None,
    authorized_namespace_type: GlobalMemoryNamespace,
    authorized_namespace_id: str,
) -> SemanticKVCacheEntry:
    if not isinstance(entry, SemanticKVCacheEntry):
        raise ValueError("semantic KV cache entry required")
    if (
        entry.namespace_type is not authorized_namespace_type
        or entry.namespace_id != authorized_namespace_id
    ):
        raise ValueError("namespace authorization mismatch")
    if entry.state is SemanticKVCacheState.INVALIDATED:
        raise ValueError("invalidated cache entry is terminal")
    if target_state is SemanticKVCacheState.ACTIVE:
        raise ValueError("governance cannot reactivate cache entry")

    invalidation_reason = None
    if target_state is SemanticKVCacheState.INVALIDATED:
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("invalidation reason required")
        invalidation_reason = reason

    payload = entry.model_dump()
    payload["state"] = target_state
    payload["creation_sequence"] = entry.creation_sequence + 1
    payload["invalidation_reason"] = invalidation_reason

    payload["cache_entry_id"] = make_semantic_kv_cache_entry_id(
        namespace_type=entry.namespace_type,
        namespace_id=entry.namespace_id,
        cache_generation=entry.cache_generation,
        semantic_key=entry.semantic_key,
        semantic_fingerprint=entry.semantic_fingerprint,
        model_id=entry.model_id,
        model_version=entry.model_version,
        tokenizer_id=entry.tokenizer_id,
        attention_layout=entry.attention_layout,
        kv_format=entry.kv_format,
        precision=entry.precision,
        context_generation=entry.context_generation,
        source_phase8_record_ids=entry.source_phase8_record_ids,
        source_global_record_ids=entry.source_global_record_ids,
        source_prediction_ids=entry.source_prediction_ids,
        source_artifact_ids=entry.source_artifact_ids,
        dependency_cache_entry_ids=entry.dependency_cache_entry_ids,
        payload=entry.payload,
        state=target_state,
        creation_sequence=entry.creation_sequence + 1,
        invalidation_reason=invalidation_reason,
    )
    return SemanticKVCacheEntry(**payload)


def mark_cache_entry_stale(
    entry: SemanticKVCacheEntry,
    *,
    authorized_namespace_type: GlobalMemoryNamespace,
    authorized_namespace_id: str,
) -> SemanticKVCacheEntry:
    if entry.state is not SemanticKVCacheState.ACTIVE:
        raise ValueError("only ACTIVE entry may become STALE")
    return _transition(
        entry,
        target_state=SemanticKVCacheState.STALE,
        reason=None,
        authorized_namespace_type=authorized_namespace_type,
        authorized_namespace_id=authorized_namespace_id,
    )


def invalidate_cache_entry(
    entry: SemanticKVCacheEntry,
    *,
    reason: str,
    authorized_namespace_type: GlobalMemoryNamespace,
    authorized_namespace_id: str,
) -> SemanticKVCacheEntry:
    if entry.state not in (
        SemanticKVCacheState.ACTIVE,
        SemanticKVCacheState.STALE,
    ):
        raise ValueError("cache entry cannot be invalidated")
    return _transition(
        entry,
        target_state=SemanticKVCacheState.INVALIDATED,
        reason=reason,
        authorized_namespace_type=authorized_namespace_type,
        authorized_namespace_id=authorized_namespace_id,
    )


def invalidate_cache_dependencies(
    entries,
    *,
    invalidated_cache_entry_id: str,
    reason: str,
    authorized_namespace_type: GlobalMemoryNamespace,
    authorized_namespace_id: str,
):
    result = []
    for entry in tuple(entries):
        if (
            entry.namespace_type is not authorized_namespace_type
            or entry.namespace_id != authorized_namespace_id
        ):
            result.append(entry)
            continue
        if invalidated_cache_entry_id in entry.dependency_cache_entry_ids:
            result.append(
                invalidate_cache_entry(
                    entry,
                    reason=reason,
                    authorized_namespace_type=authorized_namespace_type,
                    authorized_namespace_id=authorized_namespace_id,
                )
            )
        else:
            result.append(entry)
    return tuple(result)
