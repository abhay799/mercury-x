import pytest

from mercury.global_memory.contracts import GlobalMemoryNamespace
from mercury.semantic_kv_cache.compatibility import evaluate_semantic_kv_compatibility
from mercury.semantic_kv_cache.contracts import (
    SemanticKVCacheState,
    SemanticKVLookupRequest,
    SemanticKVReuseMode,
)
from mercury.semantic_kv_cache.lookup import lookup_semantic_kv_cache
from mercury.semantic_kv_cache.store import SemanticKVCacheStore
from tests._phase11_helpers import make_entry


def request(**overrides):
    data = dict(
        namespace_type=GlobalMemoryNamespace.PROJECT,
        namespace_id="p1",
        authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
        authorized_namespace_id="p1",
        semantic_key="sem",
        semantic_fingerprint="fp",
        model_id="m",
        model_version="1",
        tokenizer_id="tok",
        attention_layout="gqa",
        kv_format="paged",
        precision="FP16",
        context_generation=1,
    )
    data.update(overrides)
    return SemanticKVLookupRequest(**data)


def test_cross_project_entry_never_leaks():
    store = SemanticKVCacheStore(entries=(make_entry(namespace_id="p2"),))
    assert lookup_semantic_kv_cache(request(), store).matches == ()


def test_prediction_hint_cannot_force_stale_reuse():
    stale = make_entry(
        state=SemanticKVCacheState.STALE,
        prediction_ids=("pred",),
    )
    result = lookup_semantic_kv_cache(
        request(),
        SemanticKVCacheStore(entries=(stale,)),
        prediction_ids=("pred",),
    )
    assert result.matches == ()


def test_semantic_match_never_implies_physical_reuse_without_physical_request():
    semantic_only_request = request(
        model_id=None,
        model_version=None,
        tokenizer_id=None,
        attention_layout=None,
        kv_format=None,
        precision=None,
    )
    result = evaluate_semantic_kv_compatibility(
        semantic_only_request,
        make_entry(),
    )
    assert result.reuse_mode is SemanticKVReuseMode.SEMANTIC_COMPATIBLE
    assert not result.physical_kv_reuse_allowed


def test_inputs_are_not_mutated_by_lookup():
    entry = make_entry()
    before = entry
    lookup_semantic_kv_cache(
        request(),
        SemanticKVCacheStore(entries=(entry,)),
    )
    assert entry == before
