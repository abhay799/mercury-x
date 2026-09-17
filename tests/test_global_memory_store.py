import pytest

from mercury.global_memory.contracts import *
from mercury.global_memory.store import (
    GlobalContextStore,
    register_global_context_record,
)


def record(**u):
    v = dict(
        namespace_type=GlobalMemoryNamespace.PROJECT,
        namespace_id="n",
        global_record_id="sha256:" + "0" * 64,
        record_version=1,
        source_session_id="s",
        source_phase8_record_ids=("r",),
        source_artifact_ids=("a",),
        source_phase="p",
        memory_type=GlobalMemoryType.VALIDATED_FACT,
        context_key="k",
        creation_sequence=1,
        lifecycle=GlobalMemoryLifecycle.ACTIVE,
        conflict_state=GlobalMemoryConflictState.CLEAR,
        provenance=("e",),
        promotion_policy_id="pp",
        retention_policy_id="rp",
    )
    v.update(u)
    return GlobalContextRecord(**v)


def test_exact_namespace_registration_and_isolation():
    r = record()
    store = register_global_context_record(
        GlobalContextStore(),
        r,
        GlobalMemoryNamespace.PROJECT,
        "n",
    )

    assert store.records_for_namespace(
        GlobalMemoryNamespace.PROJECT,
        "n",
    ) == (r,)

    with pytest.raises(ValueError):
        store.records_for_namespace(
            GlobalMemoryNamespace.PROJECT,
            "other",
        )


def test_namespace_closure_is_exact_deterministic_and_blocks_writes():
    project_a = record(namespace_id="project-a")
    project_b = record(
        namespace_id="project-b",
        global_record_id="sha256:" + "1" * 64,
    )

    store = GlobalContextStore()
    store = register_global_context_record(
        store,
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

    open_fingerprint = store.fingerprint

    store = store.close_namespace(
        GlobalMemoryNamespace.PROJECT,
        "project-a",
        closure_reason="phase9-governance",
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

    metadata = store.get_namespace_closure_metadata(
        GlobalMemoryNamespace.PROJECT,
        "project-a",
    )

    assert metadata.namespace_type is GlobalMemoryNamespace.PROJECT
    assert metadata.namespace_id == "project-a"
    assert metadata.closed is True
    assert metadata.closure_reason == "phase9-governance"
    assert metadata.closure_sequence == 1

    assert store.fingerprint != open_fingerprint

    new_a = record(
        namespace_id="project-a",
        global_record_id="sha256:" + "2" * 64,
        creation_sequence=2,
    )

    with pytest.raises(ValueError):
        register_global_context_record(
            store,
            new_a,
            GlobalMemoryNamespace.PROJECT,
            "project-a",
        )

    new_b = record(
        namespace_id="project-b",
        global_record_id="sha256:" + "3" * 64,
        creation_sequence=2,
    )

    store2 = register_global_context_record(
        store,
        new_b,
        GlobalMemoryNamespace.PROJECT,
        "project-b",
    )

    assert len(
        store2.records_for_namespace(
            GlobalMemoryNamespace.PROJECT,
            "project-b",
        )
    ) == 2

    same = store.close_namespace(
        GlobalMemoryNamespace.PROJECT,
        "project-a",
        closure_reason="phase9-governance",
        closure_sequence=1,
    )

    assert same == store
    assert same.fingerprint == store.fingerprint

    with pytest.raises(ValueError):
        store.close_namespace(
            GlobalMemoryNamespace.PROJECT,
            "project-a",
            closure_reason="different-policy",
            closure_sequence=1,
        )
