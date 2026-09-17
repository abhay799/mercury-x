from mercury.semantic_kv_cache.contracts import (
    SemanticKVCacheEntry,
    SemanticKVCacheState,
    SemanticKVCompatibilityResult,
    SemanticKVLookupRequest,
    SemanticKVReuseMode,
)


def evaluate_semantic_kv_compatibility(
    request: SemanticKVLookupRequest,
    entry: SemanticKVCacheEntry,
) -> SemanticKVCompatibilityResult:
    if not isinstance(request, SemanticKVLookupRequest):
        raise ValueError("semantic KV lookup request required")
    if not isinstance(entry, SemanticKVCacheEntry):
        raise ValueError("semantic KV cache entry required")

    reasons = set()

    if (
        entry.namespace_type is not request.namespace_type
        or entry.namespace_id != request.namespace_id
    ):
        reasons.add("NAMESPACE_MISMATCH")
        return SemanticKVCompatibilityResult(
            cache_entry_id=entry.cache_entry_id,
            reuse_mode=SemanticKVReuseMode.NO_REUSE,
            semantic_reuse_allowed=False,
            physical_kv_reuse_allowed=False,
            reason_codes=tuple(sorted(reasons)),
        )

    if entry.state is not SemanticKVCacheState.ACTIVE:
        reasons.add("ENTRY_NOT_ACTIVE")
        return SemanticKVCompatibilityResult(
            cache_entry_id=entry.cache_entry_id,
            reuse_mode=SemanticKVReuseMode.NO_REUSE,
            semantic_reuse_allowed=False,
            physical_kv_reuse_allowed=False,
            reason_codes=tuple(sorted(reasons)),
        )

    semantic_key_match = entry.semantic_key == request.semantic_key
    semantic_fp_match = (
        request.semantic_fingerprint is None
        or entry.semantic_fingerprint == request.semantic_fingerprint
    )

    if not semantic_key_match:
        reasons.add("SEMANTIC_KEY_MISMATCH")
        return SemanticKVCompatibilityResult(
            cache_entry_id=entry.cache_entry_id,
            reuse_mode=SemanticKVReuseMode.NO_REUSE,
            semantic_reuse_allowed=False,
            physical_kv_reuse_allowed=False,
            reason_codes=tuple(sorted(reasons)),
        )

    semantic_reuse_allowed = semantic_fp_match
    if not semantic_fp_match:
        reasons.add("SEMANTIC_FINGERPRINT_MISMATCH")

    requested_physical = any(
        value is not None
        for value in (
            request.model_id,
            request.model_version,
            request.tokenizer_id,
            request.attention_layout,
            request.kv_format,
            request.precision,
        )
    )

    physical_match = False
    if requested_physical:
        checks = (
            ("MODEL_ID_MISMATCH", entry.model_id, request.model_id),
            ("MODEL_VERSION_MISMATCH", entry.model_version, request.model_version),
            ("TOKENIZER_MISMATCH", entry.tokenizer_id, request.tokenizer_id),
            ("ATTENTION_LAYOUT_MISMATCH", entry.attention_layout, request.attention_layout),
            ("KV_FORMAT_MISMATCH", entry.kv_format, request.kv_format),
            ("PRECISION_MISMATCH", entry.precision, request.precision),
        )
        complete_request = all(expected is not None for _, _, expected in checks)
        if not complete_request:
            reasons.add("INCOMPLETE_PHYSICAL_REQUEST")
        else:
            for code, actual, expected in checks:
                if actual != expected:
                    reasons.add(code)
            if entry.context_generation != request.context_generation:
                reasons.add("CONTEXT_GENERATION_MISMATCH")
            if entry.payload is None:
                reasons.add("MISSING_PHYSICAL_PAYLOAD")
            physical_match = (
                semantic_reuse_allowed
                and not reasons
                and entry.payload is not None
            )

    if physical_match:
        mode = SemanticKVReuseMode.EXACT
    elif semantic_reuse_allowed:
        mode = SemanticKVReuseMode.SEMANTIC_COMPATIBLE
        reasons.add("SEMANTIC_REUSE_ONLY")
    else:
        mode = SemanticKVReuseMode.NO_REUSE

    return SemanticKVCompatibilityResult(
        cache_entry_id=entry.cache_entry_id,
        reuse_mode=mode,
        semantic_reuse_allowed=semantic_reuse_allowed,
        physical_kv_reuse_allowed=physical_match,
        reason_codes=tuple(sorted(reasons)),
    )
