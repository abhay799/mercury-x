import hashlib
import json

from mercury.global_memory.contracts import GlobalMemoryNamespace
from mercury.semantic_kv_cache.contracts import (
    MAX_CACHE_METADATA_BYTES,
    SemanticKVCacheEntry,
)


def _canonical_bytes(payload) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def make_semantic_cache_key(
    *,
    namespace_type: GlobalMemoryNamespace,
    namespace_id: str,
    context_key: str,
    normalized_context: str,
    source_record_ids=(),
    source_artifact_ids=(),
    context_generation: int = 1,
) -> str:
    if not isinstance(namespace_id, str) or not namespace_id.strip():
        raise ValueError("namespace_id must be nonblank")
    if not isinstance(context_key, str) or not context_key.strip():
        raise ValueError("context_key must be nonblank")
    if not isinstance(normalized_context, str) or not normalized_context.strip():
        raise ValueError("normalized_context must be nonblank")
    if context_generation < 1:
        raise ValueError("context_generation must be positive")

    record_ids = tuple(sorted(set(source_record_ids)))
    artifact_ids = tuple(sorted(set(source_artifact_ids)))
    if any(not isinstance(x, str) or not x.strip() for x in record_ids + artifact_ids):
        raise ValueError("semantic identity sources must be nonblank")

    return hashlib.sha256(
        _canonical_bytes(
            {
                "namespace_type": namespace_type.value,
                "namespace_id": namespace_id,
                "context_key": context_key,
                "normalized_context": normalized_context,
                "source_record_ids": list(record_ids),
                "source_artifact_ids": list(artifact_ids),
                "context_generation": context_generation,
            }
        )
    ).hexdigest()


def canonical_cache_metadata_payload(entry: SemanticKVCacheEntry) -> dict:
    if not isinstance(entry, SemanticKVCacheEntry):
        raise ValueError("semantic KV cache entry required")
    return entry.model_dump(mode="json")


def validate_cache_metadata_size(entry: SemanticKVCacheEntry) -> int:
    size = len(_canonical_bytes(canonical_cache_metadata_payload(entry)))
    if size > MAX_CACHE_METADATA_BYTES:
        raise ValueError("cache metadata exceeds certified byte limit")
    return size


def make_cache_metadata_fingerprint(entry: SemanticKVCacheEntry) -> str:
    validate_cache_metadata_size(entry)
    return hashlib.sha256(
        _canonical_bytes(canonical_cache_metadata_payload(entry))
    ).hexdigest()
