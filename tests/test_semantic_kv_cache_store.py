import pytest

from mercury.global_memory.contracts import GlobalMemoryNamespace
from mercury.semantic_kv_cache.store import (
    SemanticKVCacheStore,
    register_cache_entry,
)
from tests._phase11_helpers import make_entry


def test_store_registration_is_immutable_and_deterministic():
    store = SemanticKVCacheStore()
    entry = make_entry()
    updated = register_cache_entry(
        store,
        entry,
        authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
        authorized_namespace_id="p1",
    )
    assert store.entries == ()
    assert updated.entries == (entry,)
    assert updated.fingerprint == updated.fingerprint


def test_cross_namespace_registration_fails_closed():
    with pytest.raises(ValueError):
        register_cache_entry(
            SemanticKVCacheStore(),
            make_entry(namespace_id="p1"),
            authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
            authorized_namespace_id="p2",
        )


def test_exact_duplicate_is_idempotent():
    entry = make_entry()
    store = register_cache_entry(
        SemanticKVCacheStore(),
        entry,
        authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
        authorized_namespace_id="p1",
    )
    assert register_cache_entry(
        store,
        entry,
        authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
        authorized_namespace_id="p1",
    ) == store
