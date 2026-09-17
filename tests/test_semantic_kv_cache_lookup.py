from mercury.global_memory.contracts import GlobalMemoryNamespace
from mercury.semantic_kv_cache.contracts import SemanticKVLookupRequest
from mercury.semantic_kv_cache.lookup import lookup_semantic_kv_cache
from mercury.semantic_kv_cache.store import SemanticKVCacheStore
from tests._phase11_helpers import make_entry


def request():
    return SemanticKVLookupRequest(
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


def test_prediction_hint_is_priority_only():
    a = make_entry(prediction_ids=("pred-a",), creation_sequence=1)
    b = make_entry(prediction_ids=("pred-b",), creation_sequence=2)
    store = SemanticKVCacheStore(entries=(a, b))
    result = lookup_semantic_kv_cache(
        request(),
        store,
        prediction_ids=("pred-b",),
    )
    assert result.matches[0].entry.source_prediction_ids == ("pred-b",)


def test_lookup_is_permutation_invariant_without_hint():
    a = make_entry(creation_sequence=1)
    b = make_entry(creation_sequence=2)
    first = lookup_semantic_kv_cache(
        request(),
        SemanticKVCacheStore(entries=(a, b)),
    )
    second = lookup_semantic_kv_cache(
        request(),
        SemanticKVCacheStore(entries=(b, a)),
    )
    assert first == second
