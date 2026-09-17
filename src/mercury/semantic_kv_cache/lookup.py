from mercury.semantic_kv_cache.compatibility import (
    evaluate_semantic_kv_compatibility,
)
from mercury.semantic_kv_cache.contracts import (
    MAX_CACHE_LOOKUP_RESULTS,
    SemanticKVLookupMatch,
    SemanticKVLookupRequest,
    SemanticKVLookupResult,
    SemanticKVReuseMode,
)
from mercury.semantic_kv_cache.store import SemanticKVCacheStore


REUSE_ORDER = {
    SemanticKVReuseMode.EXACT: 0,
    SemanticKVReuseMode.SEMANTIC_COMPATIBLE: 1,
    SemanticKVReuseMode.NO_REUSE: 2,
}


def lookup_semantic_kv_cache(
    request: SemanticKVLookupRequest,
    store: SemanticKVCacheStore,
    *,
    prediction_ids=(),
) -> SemanticKVLookupResult:
    if not isinstance(request, SemanticKVLookupRequest):
        raise ValueError("semantic KV lookup request required")
    if not isinstance(store, SemanticKVCacheStore):
        raise ValueError("semantic KV cache store required")

    hints = tuple(sorted(set(prediction_ids)))
    if any(not isinstance(value, str) or not value.strip() for value in hints):
        raise ValueError("prediction hint must be nonblank")

    matches = []
    for entry in store.namespace_entries(
        request.namespace_type,
        request.namespace_id,
    ):
        compatibility = evaluate_semantic_kv_compatibility(request, entry)
        if compatibility.reuse_mode is SemanticKVReuseMode.NO_REUSE:
            continue
        matches.append(
            SemanticKVLookupMatch(
                entry=entry,
                compatibility=compatibility,
            )
        )

    def key(match):
        entry = match.entry
        hinted = 0 if set(entry.source_prediction_ids) & set(hints) else 1
        return (
            REUSE_ORDER[match.compatibility.reuse_mode],
            hinted,
            entry.semantic_key,
            entry.model_id or "",
            entry.model_version or "",
            entry.context_generation,
            entry.creation_sequence,
            entry.cache_entry_id,
        )

    ordered = tuple(sorted(matches, key=key))
    limit = min(request.limit, MAX_CACHE_LOOKUP_RESULTS)
    return SemanticKVLookupResult(matches=ordered[:limit])
