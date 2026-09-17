from mercury.global_memory.contracts import GlobalMemoryNamespace
from mercury.semantic_kv_cache.contracts import (
    SemanticKVCacheEntry,
    SemanticKVCacheState,
    SemanticKVPayloadReference,
    make_semantic_kv_cache_entry_id,
)


def make_entry(
    *,
    namespace_id="p1",
    semantic_key="sem",
    semantic_fingerprint="fp",
    model_id="m",
    model_version="1",
    tokenizer_id="tok",
    attention_layout="gqa",
    kv_format="paged",
    precision="FP16",
    context_generation=1,
    payload=True,
    state=SemanticKVCacheState.ACTIVE,
    creation_sequence=1,
    prediction_ids=("pred1",),
    dependencies=(),
    invalidation_reason=None,
):
    payload_ref = None
    if payload:
        payload_ref = SemanticKVPayloadReference(
            payload_backend="test",
            payload_reference="ref",
            payload_fingerprint="payload-fp",
            payload_size_bytes=128,
        )
    kwargs = dict(
        namespace_type=GlobalMemoryNamespace.PROJECT,
        namespace_id=namespace_id,
        cache_generation=1,
        semantic_key=semantic_key,
        semantic_fingerprint=semantic_fingerprint,
        model_id=model_id,
        model_version=model_version,
        tokenizer_id=tokenizer_id,
        attention_layout=attention_layout,
        kv_format=kv_format,
        precision=precision,
        context_generation=context_generation,
        source_phase8_record_ids=("s1",),
        source_global_record_ids=("g1",),
        source_prediction_ids=prediction_ids,
        source_artifact_ids=("a1",),
        dependency_cache_entry_ids=dependencies,
        payload=payload_ref,
        state=state,
        creation_sequence=creation_sequence,
        invalidation_reason=invalidation_reason,
    )
    kwargs["cache_entry_id"] = make_semantic_kv_cache_entry_id(**kwargs)
    return SemanticKVCacheEntry(**kwargs)
