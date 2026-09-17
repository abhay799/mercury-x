from hashlib import sha256
from json import dumps

from mercury.contracts.base import ContractModel
from mercury.global_memory.contracts import (
    GlobalContextRecord,
    GlobalMemoryNamespace,
    MAX_GLOBAL_RECORDS_PER_NAMESPACE,
    canonical_global_context_payload,
)


class NamespaceClosureMetadata(ContractModel):
    namespace_type: GlobalMemoryNamespace
    namespace_id: str
    closed: bool = True
    closure_reason: str
    closure_sequence: int


class GlobalContextStore(ContractModel):
    records: tuple[GlobalContextRecord, ...] = ()
    closed_namespaces: tuple[NamespaceClosureMetadata, ...] = ()

    def records_for_namespace(self, namespace_type, namespace_id):
        values = tuple(
            x
            for x in self.records
            if x.namespace_type is namespace_type
            and x.namespace_id == namespace_id
        )
        if not values:
            raise ValueError("cross-namespace or unknown access rejected")
        return values

    def is_namespace_closed(self, namespace_type, namespace_id):
        _validate_namespace_identity(namespace_type, namespace_id)
        return any(
            item.namespace_type is namespace_type
            and item.namespace_id == namespace_id
            for item in self.closed_namespaces
        )

    def get_namespace_closure_metadata(self, namespace_type, namespace_id):
        _validate_namespace_identity(namespace_type, namespace_id)
        for item in self.closed_namespaces:
            if (
                item.namespace_type is namespace_type
                and item.namespace_id == namespace_id
            ):
                return item
        raise ValueError("namespace is not closed")

    def close_namespace(
        self,
        namespace_type,
        namespace_id,
        *,
        closure_reason,
        closure_sequence,
    ):
        _validate_namespace_identity(namespace_type, namespace_id)

        if not isinstance(closure_reason, str) or not closure_reason.strip():
            raise ValueError("closure reason required")

        if (
            not isinstance(closure_sequence, int)
            or isinstance(closure_sequence, bool)
            or closure_sequence <= 0
        ):
            raise ValueError("positive closure sequence required")

        proposed = NamespaceClosureMetadata(
            namespace_type=namespace_type,
            namespace_id=namespace_id,
            closed=True,
            closure_reason=closure_reason.strip(),
            closure_sequence=closure_sequence,
        )

        existing = {
            (item.namespace_type, item.namespace_id): item
            for item in self.closed_namespaces
        }
        key = (namespace_type, namespace_id)

        if key in existing:
            if existing[key] == proposed:
                return self
            raise ValueError("conflicting namespace closure metadata")

        existing[key] = proposed

        closures = tuple(
            sorted(
                existing.values(),
                key=lambda item: (
                    item.namespace_type.value,
                    item.namespace_id,
                    item.closure_sequence,
                    item.closure_reason,
                ),
            )
        )

        return GlobalContextStore(
            records=self.records,
            closed_namespaces=closures,
        )

    @property
    def fingerprint(self):
        payload = {
            "records": sorted(
                [canonical_global_context_payload(record) for record in self.records],
                key=str,
            ),
            "closed_namespaces": sorted(
                [
                    {
                        "namespace_type": item.namespace_type.value,
                        "namespace_id": item.namespace_id,
                        "closed": item.closed,
                        "closure_reason": item.closure_reason,
                        "closure_sequence": item.closure_sequence,
                    }
                    for item in self.closed_namespaces
                ],
                key=lambda item: (
                    item["namespace_type"],
                    item["namespace_id"],
                    item["closure_sequence"],
                    item["closure_reason"],
                ),
            ),
        }

        return "sha256:" + sha256(
            dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()


def _validate_namespace_identity(namespace_type, namespace_id):
    if not isinstance(namespace_type, GlobalMemoryNamespace):
        raise ValueError("certified namespace required")

    if not isinstance(namespace_id, str) or not namespace_id.strip():
        raise ValueError("namespace id required")


def register_global_context_record(
    store,
    record,
    authorized_namespace_type,
    authorized_namespace_id,
):
    if not isinstance(store, GlobalContextStore):
        raise ValueError("certified store required")

    if not isinstance(record, GlobalContextRecord):
        raise ValueError("certified record required")

    _validate_namespace_identity(
        authorized_namespace_type,
        authorized_namespace_id,
    )

    if (
        record.namespace_type,
        record.namespace_id,
    ) != (
        authorized_namespace_type,
        authorized_namespace_id,
    ):
        raise ValueError("namespace authorization mismatch")

    if store.is_namespace_closed(
        authorized_namespace_type,
        authorized_namespace_id,
    ):
        raise ValueError("closed namespace rejects writes")

    existing = {item.global_record_id: item for item in store.records}

    if (
        record.global_record_id in existing
        and existing[record.global_record_id] != record
    ):
        raise ValueError("conflicting duplicate identity")

    existing[record.global_record_id] = record

    namespace_count = sum(
        item.namespace_type is record.namespace_type
        and item.namespace_id == record.namespace_id
        for item in existing.values()
    )

    if namespace_count > MAX_GLOBAL_RECORDS_PER_NAMESPACE:
        raise ValueError("namespace cap exceeded")

    records = tuple(
        sorted(
            existing.values(),
            key=lambda item: (
                item.namespace_type.value,
                item.namespace_id,
                item.creation_sequence,
                item.global_record_id,
            ),
        )
    )

    return GlobalContextStore(
        records=records,
        closed_namespaces=store.closed_namespaces,
    )
