from mercury.disaggregated_execution.contracts import (
    DisaggregatedExecutionPlan,
    ExecutionHandoff,
    ExecutionHandoffKind,
)
from mercury.semantic_kv_cache.contracts import (
    SemanticKVCacheEntry,
    SemanticKVCacheState,
    SemanticKVCompatibilityResult,
)


def validate_kv_handoff_reference(
    handoff: ExecutionHandoff,
    cache_entry: SemanticKVCacheEntry,
    compatibility_result: SemanticKVCompatibilityResult,
) -> None:
    if handoff.handoff_kind is not ExecutionHandoffKind.KV_REFERENCE:
        raise ValueError("KV reference handoff required")
    if cache_entry.state is not SemanticKVCacheState.ACTIVE:
        raise ValueError("KV cache entry must be ACTIVE")
    if (
        handoff.namespace_type is not cache_entry.namespace_type
        or handoff.namespace_id != cache_entry.namespace_id
    ):
        raise ValueError("KV handoff namespace mismatch")
    if not compatibility_result.semantic_reuse_allowed:
        raise ValueError("Phase 11 denied semantic reuse")
    if compatibility_result.cache_entry_id != cache_entry.cache_entry_id:
        raise ValueError("compatibility result cache entry mismatch")
    if cache_entry.payload is not None:
        if handoff.payload_fingerprint != cache_entry.payload.payload_fingerprint:
            raise ValueError("KV payload fingerprint mismatch")
        if not compatibility_result.physical_kv_reuse_allowed:
            raise ValueError("Phase 11 denied physical KV reuse")


def validate_context_handoff_reference(
    handoff: ExecutionHandoff,
    *,
    authorized_namespace_type,
    authorized_namespace_id,
) -> None:
    if handoff.handoff_kind is not ExecutionHandoffKind.CONTEXT:
        raise ValueError("context handoff required")
    if (
        handoff.namespace_type is not authorized_namespace_type
        or handoff.namespace_id != authorized_namespace_id
    ):
        raise ValueError("context handoff namespace authorization mismatch")


def apply_prediction_hints(
    plan: DisaggregatedExecutionPlan,
    prediction_ids=(),
) -> DisaggregatedExecutionPlan:
    # Hints are deliberately advisory-only in Phase 12 baseline.
    hints = tuple(sorted(set(prediction_ids)))
    if any(not isinstance(value, str) or not value.strip() for value in hints):
        raise ValueError("prediction hints must be nonblank")
    return plan
