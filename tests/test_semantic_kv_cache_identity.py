import pytest

from mercury.global_memory.contracts import GlobalMemoryNamespace
from mercury.semantic_kv_cache.identity import make_semantic_cache_key


def test_semantic_identity_is_permutation_invariant():
    a = make_semantic_cache_key(
        namespace_type=GlobalMemoryNamespace.PROJECT,
        namespace_id="p1",
        context_key="risk",
        normalized_context="abc",
        source_record_ids=("r2", "r1"),
        source_artifact_ids=("a2", "a1"),
        context_generation=1,
    )
    b = make_semantic_cache_key(
        namespace_type=GlobalMemoryNamespace.PROJECT,
        namespace_id="p1",
        context_key="risk",
        normalized_context="abc",
        source_record_ids=("r1", "r2"),
        source_artifact_ids=("a1", "a2"),
        context_generation=1,
    )
    assert a == b


def test_namespace_participates_in_semantic_identity():
    a = make_semantic_cache_key(
        namespace_type=GlobalMemoryNamespace.PROJECT,
        namespace_id="p1",
        context_key="risk",
        normalized_context="abc",
    )
    b = make_semantic_cache_key(
        namespace_type=GlobalMemoryNamespace.PROJECT,
        namespace_id="p2",
        context_key="risk",
        normalized_context="abc",
    )
    assert a != b
