from mercury.global_memory.contracts import GlobalMemoryNamespace
from mercury.semantic_kv_cache.compatibility import evaluate_semantic_kv_compatibility
from mercury.semantic_kv_cache.contracts import (
    SemanticKVCacheState,
    SemanticKVLookupRequest,
    SemanticKVReuseMode,
)
from tests._phase11_helpers import make_entry


def req(**overrides):
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


def test_exact_physical_reuse_requires_full_compatibility():
    result = evaluate_semantic_kv_compatibility(req(), make_entry())
    assert result.reuse_mode is SemanticKVReuseMode.EXACT
    assert result.semantic_reuse_allowed
    assert result.physical_kv_reuse_allowed


def test_semantic_only_reuse_does_not_allow_physical_kv():
    request = req(model_id=None, model_version=None, tokenizer_id=None,
                  attention_layout=None, kv_format=None, precision=None)
    result = evaluate_semantic_kv_compatibility(request, make_entry())
    assert result.reuse_mode is SemanticKVReuseMode.SEMANTIC_COMPATIBLE
    assert result.semantic_reuse_allowed
    assert not result.physical_kv_reuse_allowed


def test_every_physical_mismatch_blocks_physical_reuse():
    fields = {
        "model_id": "other",
        "model_version": "2",
        "tokenizer_id": "other",
        "attention_layout": "mha",
        "kv_format": "other",
        "precision": "BF16",
        "context_generation": 2,
    }
    for field, value in fields.items():
        result = evaluate_semantic_kv_compatibility(
            req(**{field: value}),
            make_entry(),
        )
        assert not result.physical_kv_reuse_allowed


def test_stale_entry_is_not_reusable():
    result = evaluate_semantic_kv_compatibility(
        req(),
        make_entry(state=SemanticKVCacheState.STALE),
    )
    assert result.reuse_mode is SemanticKVReuseMode.NO_REUSE
