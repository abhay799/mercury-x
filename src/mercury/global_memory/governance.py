"""Phase 9 global context governance."""

from hashlib import sha256
from json import dumps

from mercury.global_memory.contracts import (
    GlobalContextRecord,
    GlobalMemoryLifecycle,
)
from mercury.global_memory.store import GlobalContextStore


_ALLOWED_GOVERNANCE_SOURCES = {
    GlobalMemoryLifecycle.ACTIVE,
    GlobalMemoryLifecycle.SUPERSEDED,
}


def _stable_governance_id(
    prior: GlobalContextRecord,
    target_lifecycle: GlobalMemoryLifecycle,
    reason: str,
) -> str:
    payload = {
        "prior_record_id": prior.global_record_id,
        "record_version": prior.record_version + 1,
        "target_lifecycle": target_lifecycle.value,
        "reason": reason,
    }

    return "sha256:" + sha256(
        dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()


def _validate_namespace_authorization(
    namespace_type,
    namespace_id,
    authorized_namespace_type,
    authorized_namespace_id,
):
    if (
        namespace_type,
        namespace_id,
    ) != (
        authorized_namespace_type,
        authorized_namespace_id,
    ):
        raise ValueError("namespace authorization mismatch")


def _transition_global_context(
    record: GlobalContextRecord,
    *,
    target_lifecycle: GlobalMemoryLifecycle,
    authorized_namespace_type,
    authorized_namespace_id,
    reason: str,
    store: GlobalContextStore | None = None,
) -> GlobalContextRecord:
    if not isinstance(record, GlobalContextRecord):
        raise ValueError("valid global context record required")

    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("governance reason required")

    _validate_namespace_authorization(
        record.namespace_type,
        record.namespace_id,
        authorized_namespace_type,
        authorized_namespace_id,
    )

    if store is not None:
        if not isinstance(store, GlobalContextStore):
            raise ValueError("certified store required")

        if store.is_namespace_closed(
            record.namespace_type,
            record.namespace_id,
        ):
            raise ValueError(
                "governance mutation rejected after namespace closure"
            )

    if record.lifecycle not in _ALLOWED_GOVERNANCE_SOURCES:
        raise ValueError("invalid lifecycle transition")

    normalized_reason = reason.strip()

    data = record.model_dump()

    data.update(
        {
            "global_record_id": _stable_governance_id(
                record,
                target_lifecycle,
                normalized_reason,
            ),
            "record_version": record.record_version + 1,
            "creation_sequence": record.creation_sequence + 1,
            "lifecycle": target_lifecycle,
            "supersedes_record_id": record.global_record_id,
            "change_reason": normalized_reason,
        }
    )

    return GlobalContextRecord(**data)


def expire_global_context(
    record: GlobalContextRecord,
    *,
    authorized_namespace_type,
    authorized_namespace_id,
    reason: str,
    store: GlobalContextStore | None = None,
) -> GlobalContextRecord:
    return _transition_global_context(
        record,
        target_lifecycle=GlobalMemoryLifecycle.EXPIRED,
        authorized_namespace_type=authorized_namespace_type,
        authorized_namespace_id=authorized_namespace_id,
        reason=reason,
        store=store,
    )


def revoke_global_context(
    record: GlobalContextRecord,
    *,
    authorized_namespace_type,
    authorized_namespace_id,
    reason: str,
    store: GlobalContextStore | None = None,
) -> GlobalContextRecord:
    return _transition_global_context(
        record,
        target_lifecycle=GlobalMemoryLifecycle.REVOKED,
        authorized_namespace_type=authorized_namespace_type,
        authorized_namespace_id=authorized_namespace_id,
        reason=reason,
        store=store,
    )


def tombstone_global_context(
    record: GlobalContextRecord,
    *,
    authorized_namespace_type,
    authorized_namespace_id,
    reason: str,
    store: GlobalContextStore | None = None,
) -> GlobalContextRecord:
    return _transition_global_context(
        record,
        target_lifecycle=GlobalMemoryLifecycle.TOMBSTONED,
        authorized_namespace_type=authorized_namespace_type,
        authorized_namespace_id=authorized_namespace_id,
        reason=reason,
        store=store,
    )


def close_global_namespace(
    store: GlobalContextStore,
    *,
    namespace_type,
    namespace_id,
    authorized_namespace_type,
    authorized_namespace_id,
    reason: str,
    closure_sequence: int,
) -> GlobalContextStore:
    if not isinstance(store, GlobalContextStore):
        raise ValueError("certified store required")

    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("governance reason required")

    _validate_namespace_authorization(
        namespace_type,
        namespace_id,
        authorized_namespace_type,
        authorized_namespace_id,
    )

    return store.close_namespace(
        namespace_type,
        namespace_id,
        closure_reason=reason.strip(),
        closure_sequence=closure_sequence,
    )
