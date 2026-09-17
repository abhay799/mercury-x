import hashlib
import json

from pydantic import field_validator

from mercury.contracts.base import ContractModel
from mercury.global_memory.contracts import GlobalMemoryNamespace
from mercury.semantic_kv_cache.contracts import (
    MAX_KV_CACHE_ENTRIES_PER_NAMESPACE,
    SemanticKVCacheEntry,
)
from mercury.semantic_kv_cache.identity import validate_cache_metadata_size


class SemanticKVCacheStore(ContractModel):
    entries: tuple[SemanticKVCacheEntry, ...] = ()

    @field_validator("entries")
    @classmethod
    def validate_entries(cls, value):
        entries = tuple(value)
        ids = tuple(entry.cache_entry_id for entry in entries)
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate cache entry id")
        per_namespace = {}
        for entry in entries:
            key = (entry.namespace_type, entry.namespace_id)
            per_namespace[key] = per_namespace.get(key, 0) + 1
            if per_namespace[key] > MAX_KV_CACHE_ENTRIES_PER_NAMESPACE:
                raise ValueError("cache namespace capacity exceeded")
        return entries

    def namespace_entries(
        self,
        namespace_type: GlobalMemoryNamespace,
        namespace_id: str,
    ) -> tuple[SemanticKVCacheEntry, ...]:
        return tuple(
            entry
            for entry in self.entries
            if entry.namespace_type is namespace_type
            and entry.namespace_id == namespace_id
        )

    @property
    def fingerprint(self) -> str:
        payload = [
            entry.model_dump(mode="json")
            for entry in sorted(
                self.entries,
                key=lambda x: (
                    x.namespace_type.value,
                    x.namespace_id,
                    x.cache_entry_id,
                ),
            )
        ]
        encoded = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


def register_cache_entry(
    store: SemanticKVCacheStore,
    entry: SemanticKVCacheEntry,
    *,
    authorized_namespace_type: GlobalMemoryNamespace,
    authorized_namespace_id: str,
    global_context_store=None,
) -> SemanticKVCacheStore:
    if not isinstance(store, SemanticKVCacheStore):
        raise ValueError("semantic KV cache store required")
    if not isinstance(entry, SemanticKVCacheEntry):
        raise ValueError("semantic KV cache entry required")
    if (
        entry.namespace_type is not authorized_namespace_type
        or entry.namespace_id != authorized_namespace_id
    ):
        raise ValueError("namespace authorization mismatch")

    if global_context_store is not None:
        if global_context_store.is_namespace_closed(
            entry.namespace_type,
            entry.namespace_id,
        ):
            raise ValueError("closed namespace cannot accept cache entry")

    validate_cache_metadata_size(entry)

    existing = {item.cache_entry_id: item for item in store.entries}
    if entry.cache_entry_id in existing:
        if existing[entry.cache_entry_id] == entry:
            return store
        raise ValueError("conflicting duplicate cache identity")

    count = len(
        store.namespace_entries(
            entry.namespace_type,
            entry.namespace_id,
        )
    )
    if count >= MAX_KV_CACHE_ENTRIES_PER_NAMESPACE:
        raise ValueError("cache namespace capacity exceeded")

    return SemanticKVCacheStore(entries=store.entries + (entry,))
