import importlib.util

import pytest

from mercury.global_memory.contracts import (
    GlobalContextRecord,
    GlobalMemoryConflictState,
    GlobalMemoryLifecycle,
    GlobalMemoryNamespace,
    GlobalMemoryQuery,
    GlobalMemoryType,
)
from mercury.global_memory.store import (
    GlobalContextStore,
    register_global_context_record,
)


def record():
    return GlobalContextRecord(
        namespace_type=GlobalMemoryNamespace.PROJECT,
        namespace_id="project-a",
        global_record_id="sha256:" + "1" * 64,
        record_version=1,
        source_session_id="session-1",
        source_phase8_record_ids=("phase8-record-1",),
        source_artifact_ids=("artifact-1",),
        source_phase="phase8",
        memory_type=GlobalMemoryType.VALIDATED_FACT,
        context_key="customer-risk",
        creation_sequence=1,
        lifecycle=GlobalMemoryLifecycle.ACTIVE,
        conflict_state=GlobalMemoryConflictState.CLEAR,
        provenance=("evidence-1",),
        promotion_policy_id="promotion-policy-1",
        retention_policy_id="retention-policy-1",
    )


def test_phase9_governance_module_exists():
    assert importlib.util.find_spec(
        "mercury.global_memory.governance"
    ) is not None


def test_expire_global_context_creates_immutable_expired_version():
    from mercury.global_memory.governance import expire_global_context

    original = record()

    expired = expire_global_context(
        original,
        authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
        authorized_namespace_id="project-a",
        reason="retention-expired",
    )

    assert original.lifecycle is GlobalMemoryLifecycle.ACTIVE
    assert original.record_version == 1

    assert expired is not original
    assert expired.lifecycle is GlobalMemoryLifecycle.EXPIRED

    assert expired.namespace_type is original.namespace_type
    assert expired.namespace_id == original.namespace_id
    assert expired.context_key == original.context_key

    assert expired.record_version == 2
    assert expired.creation_sequence == 2
    assert expired.supersedes_record_id == original.global_record_id

    assert (
        expired.source_phase8_record_ids
        == original.source_phase8_record_ids
    )
    assert expired.source_artifact_ids == original.source_artifact_ids
    assert expired.provenance == original.provenance
    assert expired.promotion_policy_id == original.promotion_policy_id
    assert expired.retention_policy_id == original.retention_policy_id

    assert expired.global_record_id != original.global_record_id


def test_expire_global_context_rejects_namespace_authorization_mismatch():
    from mercury.global_memory.governance import expire_global_context

    original = record()

    with pytest.raises(ValueError):
        expire_global_context(
            original,
            authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
            authorized_namespace_id="other-project",
            reason="retention-expired",
        )


def test_expire_global_context_rejects_terminal_reactivation_or_reexpiry():
    from mercury.global_memory.governance import expire_global_context

    original = record()

    expired = expire_global_context(
        original,
        authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
        authorized_namespace_id="project-a",
        reason="retention-expired",
    )

    with pytest.raises(ValueError):
        expire_global_context(
            expired,
            authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
            authorized_namespace_id="project-a",
            reason="expire-again",
        )


def test_revoke_global_context_creates_immutable_revoked_version():
    from mercury.global_memory.governance import revoke_global_context

    original = record()

    revoked = revoke_global_context(
        original,
        authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
        authorized_namespace_id="project-a",
        reason="promotion-revoked",
    )

    assert original.lifecycle is GlobalMemoryLifecycle.ACTIVE
    assert original.record_version == 1

    assert revoked is not original
    assert revoked.lifecycle is GlobalMemoryLifecycle.REVOKED

    assert revoked.namespace_type is original.namespace_type
    assert revoked.namespace_id == original.namespace_id
    assert revoked.context_key == original.context_key

    assert revoked.record_version == 2
    assert revoked.creation_sequence == 2
    assert revoked.supersedes_record_id == original.global_record_id

    assert (
        revoked.source_phase8_record_ids
        == original.source_phase8_record_ids
    )
    assert revoked.source_artifact_ids == original.source_artifact_ids
    assert revoked.provenance == original.provenance
    assert revoked.promotion_policy_id == original.promotion_policy_id
    assert revoked.retention_policy_id == original.retention_policy_id

    assert revoked.global_record_id != original.global_record_id


def test_tombstone_global_context_creates_immutable_tombstoned_version():
    from mercury.global_memory.governance import tombstone_global_context

    original = record()

    tombstoned = tombstone_global_context(
        original,
        authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
        authorized_namespace_id="project-a",
        reason="governance-tombstone",
    )

    assert original.lifecycle is GlobalMemoryLifecycle.ACTIVE
    assert original.record_version == 1

    assert tombstoned is not original
    assert tombstoned.lifecycle is GlobalMemoryLifecycle.TOMBSTONED

    assert tombstoned.namespace_type is original.namespace_type
    assert tombstoned.namespace_id == original.namespace_id
    assert tombstoned.context_key == original.context_key

    assert tombstoned.record_version == 2
    assert tombstoned.creation_sequence == 2
    assert tombstoned.supersedes_record_id == original.global_record_id

    assert (
        tombstoned.source_phase8_record_ids
        == original.source_phase8_record_ids
    )
    assert tombstoned.source_artifact_ids == original.source_artifact_ids
    assert tombstoned.provenance == original.provenance
    assert tombstoned.promotion_policy_id == original.promotion_policy_id
    assert tombstoned.retention_policy_id == original.retention_policy_id

    assert tombstoned.global_record_id != original.global_record_id


def test_close_global_namespace_closes_exact_namespace_only():
    from mercury.global_memory.governance import close_global_namespace

    store = GlobalContextStore()

    store = close_global_namespace(
        store,
        namespace_type=GlobalMemoryNamespace.PROJECT,
        namespace_id="project-a",
        authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
        authorized_namespace_id="project-a",
        reason="project-closed",
        closure_sequence=1,
    )

    assert store.is_namespace_closed(
        GlobalMemoryNamespace.PROJECT,
        "project-a",
    )

    assert not store.is_namespace_closed(
        GlobalMemoryNamespace.PROJECT,
        "project-b",
    )


def test_close_global_namespace_rejects_authorization_mismatch():
    from mercury.global_memory.governance import close_global_namespace

    store = GlobalContextStore()

    with pytest.raises(ValueError):
        close_global_namespace(
            store,
            namespace_type=GlobalMemoryNamespace.PROJECT,
            namespace_id="project-a",
            authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
            authorized_namespace_id="project-b",
            reason="project-closed",
            closure_sequence=1,
        )


def test_governance_mutation_rejected_after_namespace_closure():
    from mercury.global_memory.governance import (
        close_global_namespace,
        expire_global_context,
    )

    original = record()

    store = register_global_context_record(
        GlobalContextStore(),
        original,
        GlobalMemoryNamespace.PROJECT,
        "project-a",
    )

    store = close_global_namespace(
        store,
        namespace_type=GlobalMemoryNamespace.PROJECT,
        namespace_id="project-a",
        authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
        authorized_namespace_id="project-a",
        reason="project-closed",
        closure_sequence=1,
    )

    with pytest.raises(ValueError):
        expire_global_context(
            original,
            authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
            authorized_namespace_id="project-a",
            reason="should-fail-after-close",
            store=store,
        )


def test_retrieval_excludes_expired_revoked_and_tombstoned_records():
    from mercury.global_memory.governance import (
        expire_global_context,
        revoke_global_context,
        tombstone_global_context,
    )
    from mercury.global_memory.retrieval import retrieve_global_context

    original = record()

    expired = expire_global_context(
        original,
        authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
        authorized_namespace_id="project-a",
        reason="expired",
    )

    revoked = revoke_global_context(
        original,
        authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
        authorized_namespace_id="project-a",
        reason="revoked",
    )

    tombstoned = tombstone_global_context(
        original,
        authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
        authorized_namespace_id="project-a",
        reason="tombstoned",
    )

    store = GlobalContextStore(
        records=(
            original,
            expired,
            revoked,
            tombstoned,
        )
    )

    query = GlobalMemoryQuery(
        namespace_type=GlobalMemoryNamespace.PROJECT,
        namespace_id="project-a",
        authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
        authorized_namespace_id="project-a",
    )

    result = retrieve_global_context(
        query,
        store,
    )

    assert result.records == (original,)


def test_closed_namespace_rejects_future_registration():
    from mercury.global_memory.governance import close_global_namespace

    original = record()

    store = register_global_context_record(
        GlobalContextStore(),
        original,
        GlobalMemoryNamespace.PROJECT,
        "project-a",
    )

    store = close_global_namespace(
        store,
        namespace_type=GlobalMemoryNamespace.PROJECT,
        namespace_id="project-a",
        authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
        authorized_namespace_id="project-a",
        reason="project-closed",
        closure_sequence=1,
    )

    new_record = record().model_copy(
        update={
            "global_record_id": "sha256:" + "2" * 64,
            "creation_sequence": 2,
        }
    )

    with pytest.raises(ValueError):
        register_global_context_record(
            store,
            new_record,
            GlobalMemoryNamespace.PROJECT,
            "project-a",
        )


def test_superseded_record_can_transition_to_governance_terminal_state():
    from mercury.global_memory.governance import expire_global_context

    superseded = record().model_copy(
        update={
            "lifecycle": GlobalMemoryLifecycle.SUPERSEDED,
        }
    )

    expired = expire_global_context(
        superseded,
        authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
        authorized_namespace_id="project-a",
        reason="superseded-retention-expired",
    )

    assert expired.lifecycle is GlobalMemoryLifecycle.EXPIRED
    assert expired.record_version == superseded.record_version + 1
    assert expired.supersedes_record_id == superseded.global_record_id


def test_governance_transition_is_deterministic():
    from mercury.global_memory.governance import revoke_global_context

    original = record()

    first = revoke_global_context(
        original,
        authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
        authorized_namespace_id="project-a",
        reason="deterministic-revocation",
    )

    second = revoke_global_context(
        original,
        authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
        authorized_namespace_id="project-a",
        reason="deterministic-revocation",
    )

    assert first == second
    assert first.global_record_id == second.global_record_id


def test_closing_namespace_a_does_not_block_namespace_b():
    from mercury.global_memory.governance import close_global_namespace

    project_a = record()

    project_b = record().model_copy(
        update={
            "namespace_id": "project-b",
            "global_record_id": "sha256:" + "2" * 64,
        }
    )

    store = register_global_context_record(
        GlobalContextStore(),
        project_a,
        GlobalMemoryNamespace.PROJECT,
        "project-a",
    )

    store = register_global_context_record(
        store,
        project_b,
        GlobalMemoryNamespace.PROJECT,
        "project-b",
    )

    store = close_global_namespace(
        store,
        namespace_type=GlobalMemoryNamespace.PROJECT,
        namespace_id="project-a",
        authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
        authorized_namespace_id="project-a",
        reason="project-a-closed",
        closure_sequence=1,
    )

    assert store.is_namespace_closed(
        GlobalMemoryNamespace.PROJECT,
        "project-a",
    )

    assert not store.is_namespace_closed(
        GlobalMemoryNamespace.PROJECT,
        "project-b",
    )

    project_b_next = project_b.model_copy(
        update={
            "global_record_id": "sha256:" + "3" * 64,
            "creation_sequence": 2,
        }
    )

    updated_store = register_global_context_record(
        store,
        project_b_next,
        GlobalMemoryNamespace.PROJECT,
        "project-b",
    )

    assert len(
        updated_store.records_for_namespace(
            GlobalMemoryNamespace.PROJECT,
            "project-b",
        )
    ) == 2


def test_default_current_retrieval_excludes_superseded_record():
    from mercury.global_memory.retrieval import retrieve_global_context

    active = record()

    superseded = record().model_copy(
        update={
            "global_record_id": "sha256:" + "4" * 64,
            "record_version": 2,
            "creation_sequence": 2,
            "lifecycle": GlobalMemoryLifecycle.SUPERSEDED,
            "supersedes_record_id": active.global_record_id,
            "change_reason": "new-version",
        }
    )

    store = GlobalContextStore(
        records=(
            active,
            superseded,
        )
    )

    query = GlobalMemoryQuery(
        namespace_type=GlobalMemoryNamespace.PROJECT,
        namespace_id="project-a",
        authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
        authorized_namespace_id="project-a",
    )

    result = retrieve_global_context(
        query,
        store,
    )

    assert result.records == (active,)


def test_cross_namespace_type_governance_is_rejected():
    from mercury.global_memory.governance import expire_global_context

    original = record()

    with pytest.raises(ValueError):
        expire_global_context(
            original,
            authorized_namespace_type=GlobalMemoryNamespace.WORKSPACE,
            authorized_namespace_id="project-a",
            reason="cross-namespace-type",
        )


def test_revoked_and_tombstoned_records_cannot_transition_again():
    from mercury.global_memory.governance import (
        revoke_global_context,
        tombstone_global_context,
    )

    original = record()

    revoked = revoke_global_context(
        original,
        authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
        authorized_namespace_id="project-a",
        reason="revoked",
    )

    with pytest.raises(ValueError):
        tombstone_global_context(
            revoked,
            authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
            authorized_namespace_id="project-a",
            reason="terminal-transition",
        )

    tombstoned = tombstone_global_context(
        original,
        authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
        authorized_namespace_id="project-a",
        reason="tombstoned",
    )

    with pytest.raises(ValueError):
        revoke_global_context(
            tombstoned,
            authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
            authorized_namespace_id="project-a",
            reason="terminal-transition",
        )


def test_namespace_closure_is_idempotent_and_conflicting_closure_rejected():
    from mercury.global_memory.governance import close_global_namespace

    store = GlobalContextStore()

    first = close_global_namespace(
        store,
        namespace_type=GlobalMemoryNamespace.PROJECT,
        namespace_id="project-a",
        authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
        authorized_namespace_id="project-a",
        reason="project-closed",
        closure_sequence=1,
    )

    second = close_global_namespace(
        first,
        namespace_type=GlobalMemoryNamespace.PROJECT,
        namespace_id="project-a",
        authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
        authorized_namespace_id="project-a",
        reason="project-closed",
        closure_sequence=1,
    )

    assert first == second
    assert first.fingerprint == second.fingerprint

    with pytest.raises(ValueError):
        close_global_namespace(
            second,
            namespace_type=GlobalMemoryNamespace.PROJECT,
            namespace_id="project-a",
            authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
            authorized_namespace_id="project-a",
            reason="different-closure-reason",
            closure_sequence=1,
        )


def test_retrieval_rejects_authorized_namespace_mismatch():
    from mercury.global_memory.retrieval import retrieve_global_context

    original = record()

    store = register_global_context_record(
        GlobalContextStore(),
        original,
        GlobalMemoryNamespace.PROJECT,
        "project-a",
    )

    query = GlobalMemoryQuery(
        namespace_type=GlobalMemoryNamespace.PROJECT,
        namespace_id="project-a",
        authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
        authorized_namespace_id="project-b",
    )

    with pytest.raises(ValueError):
        retrieve_global_context(
            query,
            store,
        )


def test_governance_does_not_mutate_source_record():
    from mercury.global_memory.governance import revoke_global_context

    original = record()
    before = original.model_dump()

    revoked = revoke_global_context(
        original,
        authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
        authorized_namespace_id="project-a",
        reason="immutability-check",
    )

    assert original.model_dump() == before
    assert revoked is not original
    assert revoked.provenance == original.provenance
    assert revoked.source_phase8_record_ids == original.source_phase8_record_ids
    assert revoked.source_artifact_ids == original.source_artifact_ids
    assert revoked.promotion_policy_id == original.promotion_policy_id
    assert revoked.retention_policy_id == original.retention_policy_id


def test_namespace_closure_preserves_existing_records():
    from mercury.global_memory.governance import close_global_namespace

    original = record()

    store = register_global_context_record(
        GlobalContextStore(),
        original,
        GlobalMemoryNamespace.PROJECT,
        "project-a",
    )

    closed = close_global_namespace(
        store,
        namespace_type=GlobalMemoryNamespace.PROJECT,
        namespace_id="project-a",
        authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
        authorized_namespace_id="project-a",
        reason="project-closed",
        closure_sequence=1,
    )

    assert closed.records_for_namespace(
        GlobalMemoryNamespace.PROJECT,
        "project-a",
    ) == (original,)


def test_phase9_exposes_no_user_profile_memory_type():
    assert "USER_PROFILE" not in GlobalMemoryType.__members__