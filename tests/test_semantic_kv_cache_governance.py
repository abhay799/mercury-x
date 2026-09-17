import pytest

from mercury.global_memory.contracts import GlobalMemoryNamespace
from mercury.semantic_kv_cache.contracts import SemanticKVCacheState
from mercury.semantic_kv_cache.governance import (
    invalidate_cache_dependencies,
    invalidate_cache_entry,
    mark_cache_entry_stale,
)
from tests._phase11_helpers import make_entry


def test_stale_transition_is_immutable():
    source = make_entry()
    stale = mark_cache_entry_stale(
        source,
        authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
        authorized_namespace_id="p1",
    )
    assert source.state is SemanticKVCacheState.ACTIVE
    assert stale.state is SemanticKVCacheState.STALE
    assert stale.cache_entry_id != source.cache_entry_id


def test_invalidation_requires_reason_and_is_terminal():
    source = make_entry()
    invalidated = invalidate_cache_entry(
        source,
        reason="upstream changed",
        authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
        authorized_namespace_id="p1",
    )
    assert invalidated.state is SemanticKVCacheState.INVALIDATED
    with pytest.raises(ValueError):
        invalidate_cache_entry(
            invalidated,
            reason="again",
            authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
            authorized_namespace_id="p1",
        )


def test_dependency_invalidation_is_explicit_only():
    parent = make_entry()
    child = make_entry(
        creation_sequence=2,
        dependencies=(parent.cache_entry_id,),
    )
    other = make_entry(creation_sequence=3)
    result = invalidate_cache_dependencies(
        (child, other),
        invalidated_cache_entry_id=parent.cache_entry_id,
        reason="dependency invalidated",
        authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
        authorized_namespace_id="p1",
    )
    assert result[0].state is SemanticKVCacheState.INVALIDATED
    assert result[1].state is SemanticKVCacheState.ACTIVE
