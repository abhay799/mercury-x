"""Immutable deterministic global-context versioning and consolidation."""

from hashlib import sha256
from json import dumps

from mercury.global_memory.contracts import (
    GlobalConsolidationRequest,
    GlobalConsolidationResult,
    GlobalContextRecord,
    GlobalMemoryConflictState,
    GlobalMemoryLifecycle,
)


def _stable_id(kind, payload):
    encoded = dumps({"kind": kind, **payload}, default=str, sort_keys=True, separators=(",", ":"))
    return "sha256:" + sha256(encoded.encode()).hexdigest()


def _nonblank(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"nonblank {name} required")
    return value


def _nonblank_tuple(values, name):
    try:
        values = tuple(values)
    except TypeError as error:
        raise ValueError(f"{name} collection required") from error
    if not values or any(not isinstance(value, str) or not value.strip() for value in values):
        raise ValueError(f"nonblank {name} required")
    return tuple(sorted(set(values)))


def create_global_record_version(
    prior: GlobalContextRecord,
    *,
    change_reason: str,
    supersedes_record_id: str | None = None,
    namespace_type=None,
    namespace_id: str | None = None,
    context_key: str | None = None,
    provenance=None,
    source_phase8_record_ids=None,
    source_artifact_ids=None,
    promotion_policy_id: str | None = None,
    retention_policy_id: str | None = None,
) -> GlobalContextRecord:
    """Create the exact next immutable version of a global context record."""
    if not isinstance(prior, GlobalContextRecord):
        raise ValueError("valid prior record required")
    _nonblank(change_reason, "change reason")
    if supersedes_record_id is not None and supersedes_record_id != prior.global_record_id:
        raise ValueError("supersedes record id must match prior record")
    if namespace_type is not None and namespace_type is not prior.namespace_type:
        raise ValueError("namespace supersession mismatch")
    if namespace_id is not None and namespace_id != prior.namespace_id:
        raise ValueError("namespace supersession mismatch")
    if context_key is not None and context_key != prior.context_key:
        raise ValueError("context key lineage mismatch")
    new_provenance = prior.provenance if provenance is None else _nonblank_tuple(provenance, "provenance")
    if not set(prior.provenance).issubset(new_provenance):
        raise ValueError("prior provenance must remain traceable")
    new_phase8_ids = prior.source_phase8_record_ids if source_phase8_record_ids is None else _nonblank_tuple(source_phase8_record_ids, "source lineage")
    if not set(prior.source_phase8_record_ids).issubset(new_phase8_ids):
        raise ValueError("prior source lineage must remain traceable")
    new_artifact_ids = prior.source_artifact_ids if source_artifact_ids is None else _nonblank_tuple(source_artifact_ids, "source artifacts")
    if not set(prior.source_artifact_ids).issubset(new_artifact_ids):
        raise ValueError("prior source artifacts must remain traceable")
    data = prior.model_dump()
    data.update({
        "global_record_id": "pending",
        "record_version": prior.record_version + 1,
        "creation_sequence": prior.creation_sequence + 1,
        "supersedes_record_id": prior.global_record_id,
        "change_reason": change_reason,
        "provenance": new_provenance,
        "source_phase8_record_ids": new_phase8_ids,
        "source_artifact_ids": new_artifact_ids,
        "promotion_policy_id": prior.promotion_policy_id if promotion_policy_id is None else _nonblank(promotion_policy_id, "promotion policy id"),
        "retention_policy_id": prior.retention_policy_id if retention_policy_id is None else _nonblank(retention_policy_id, "retention policy id"),
    })
    data["global_record_id"] = _stable_id("global-record-version", {
        "prior_record_id": prior.global_record_id,
        "record_version": data["record_version"],
        "change_reason": change_reason,
        "provenance": data["provenance"],
        "source_phase8_record_ids": data["source_phase8_record_ids"],
        "source_artifact_ids": data["source_artifact_ids"],
    })
    return GlobalContextRecord(**data)


def consolidate_global_context(
    request: GlobalConsolidationRequest,
    source_records,
) -> GlobalConsolidationResult:
    """Create a deterministic, evidence-preserving summary for exact-namespace sources."""
    if not isinstance(request, GlobalConsolidationRequest):
        raise ValueError("certified consolidation request required")
    try:
        sources = tuple(source_records)
    except TypeError as error:
        raise ValueError("source records required") from error
    if not sources or len(sources) > 256:
        raise ValueError("source record count outside certified limit")
    if any(not isinstance(source, GlobalContextRecord) for source in sources):
        raise ValueError("valid source records required")
    source_ids = tuple(source.global_record_id for source in sources)
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("duplicate source record identity")
    if tuple(sorted(source_ids)) != request.source_record_ids:
        raise ValueError("source record identities do not match request")
    if any((source.namespace_type, source.namespace_id) != (request.namespace_type, request.namespace_id) for source in sources):
        raise ValueError("source namespace mismatch")
    ordered = tuple(sorted(sources, key=lambda source: source.global_record_id))
    conflict_state = (
        GlobalMemoryConflictState.CONFLICTING
        if any(source.conflict_state is GlobalMemoryConflictState.CONFLICTING for source in ordered)
        else GlobalMemoryConflictState.CLEAR
    )
    source_phase8_ids = tuple(sorted({item for source in ordered for item in source.source_phase8_record_ids}))
    source_artifact_ids = tuple(sorted({item for source in ordered for item in source.source_artifact_ids}))
    provenance = tuple(sorted({item for source in ordered for item in source.provenance}))
    payload = {
        "namespace_type": request.namespace_type.value,
        "namespace_id": request.namespace_id,
        "source_global_record_ids": tuple(source.global_record_id for source in ordered),
        "source_record_versions": tuple(source.record_version for source in ordered),
        "consolidation_method_id": request.method_id,
        "consolidation_method_version": request.method_version,
        "target_context_key": request.context_key,
        "target_memory_type": request.memory_type.value,
        "conflict_state": conflict_state.value,
    }
    summary = GlobalContextRecord(
        namespace_type=request.namespace_type,
        namespace_id=request.namespace_id,
        global_record_id=_stable_id("global-consolidation", payload),
        record_version=1,
        source_session_id=min(source.source_session_id for source in ordered),
        source_phase8_record_ids=source_phase8_ids,
        source_artifact_ids=source_artifact_ids,
        source_phase="global-consolidation",
        memory_type=request.memory_type,
        context_key=request.context_key,
        creation_sequence=max(source.creation_sequence for source in ordered) + 1,
        lifecycle=GlobalMemoryLifecycle.ACTIVE,
        conflict_state=conflict_state,
        provenance=provenance,
        promotion_policy_id=ordered[0].promotion_policy_id,
        retention_policy_id=ordered[0].retention_policy_id,
    )
    return GlobalConsolidationResult(
        status=__import__("mercury.global_memory.contracts", fromlist=["GlobalMemoryPhaseStatus"]).GlobalMemoryPhaseStatus.READY,
        record=summary,
        namespace_type=request.namespace_type,
        namespace_id=request.namespace_id,
        source_global_record_ids=tuple(source.global_record_id for source in ordered),
        source_record_versions=tuple(source.record_version for source in ordered),
        source_provenance=tuple(source.provenance for source in ordered),
        source_conflict_states=tuple(source.conflict_state for source in ordered),
        consolidation_method_id=request.method_id,
        consolidation_method_version=request.method_version,
    )
