import pytest

from mercury.global_memory.contracts import (
    GlobalContextRecord, GlobalMemoryConflictState, GlobalMemoryLifecycle,
    GlobalMemoryNamespace, GlobalMemoryQuery, GlobalMemoryType,
)
from mercury.global_memory.store import GlobalContextStore
from mercury.global_memory.retrieval import retrieve_global_context


def record(identifier, **updates):
    values = dict(
        namespace_type=GlobalMemoryNamespace.PROJECT, namespace_id="project-a",
        global_record_id=f"sha256:{identifier:064d}", record_version=1,
        source_session_id="session", source_phase8_record_ids=("phase8-a",),
        source_artifact_ids=("artifact-a",), source_phase="phase8",
        memory_type=GlobalMemoryType.VALIDATED_FACT, context_key="context",
        creation_sequence=1, lifecycle=GlobalMemoryLifecycle.ACTIVE,
        conflict_state=GlobalMemoryConflictState.CLEAR, provenance=("evidence",),
        promotion_policy_id="promotion", retention_policy_id="retention",
    )
    values.update(updates)
    return GlobalContextRecord(**values)


def query(**updates):
    values = dict(
        namespace_type=GlobalMemoryNamespace.PROJECT, namespace_id="project-a",
        authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
        authorized_namespace_id="project-a",
    )
    values.update(updates)
    return GlobalMemoryQuery(**values)


def test_retrieves_active_records_in_canonical_order():
    store = GlobalContextStore(records=(
        record(3, context_key="z", creation_sequence=1),
        record(2, context_key="a", record_version=2, creation_sequence=3),
        record(1, context_key="a", record_version=1, creation_sequence=2),
        record(4, lifecycle=GlobalMemoryLifecycle.EXPIRED),
    ))

    result = retrieve_global_context(query(), store)

    assert [item.global_record_id for item in result.records] == [
        record(1, context_key="a", record_version=1, creation_sequence=2).global_record_id,
        record(2, context_key="a", record_version=2, creation_sequence=3).global_record_id,
        record(3, context_key="z", creation_sequence=1).global_record_id,
    ]


def test_rejects_namespace_authorization_mismatch_without_fallback():
    store = GlobalContextStore(records=(record(1),))

    with pytest.raises(ValueError, match="namespace authorization mismatch"):
        retrieve_global_context(query(authorized_namespace_id="project-b"), store)


def test_applies_all_structured_filters_exactly():
    matching = record(1, memory_type=GlobalMemoryType.GLOBAL_SUMMARY,
                      source_artifact_ids=("artifact-b",),
                      source_phase8_record_ids=("phase8-a", "phase8-b"),
                      record_version=2, lifecycle=GlobalMemoryLifecycle.SUPERSEDED,
                      conflict_state=GlobalMemoryConflictState.CONFLICTING,
                      context_key="target")
    store = GlobalContextStore(records=(matching, record(2)))

    result = retrieve_global_context(query(
        memory_types=(GlobalMemoryType.GLOBAL_SUMMARY,), context_key="target",
        source_artifact_id="artifact-b", source_phase8_record_ids=("phase8-b",),
        record_version=2, lifecycle=GlobalMemoryLifecycle.SUPERSEDED,
        conflict_state=GlobalMemoryConflictState.CONFLICTING, current_only=False,
    ), store)

    assert result.records == (matching,)


def test_current_only_excludes_superseded_and_false_allows_historical_records():
    active = record(1)
    superseded = record(2, lifecycle=GlobalMemoryLifecycle.SUPERSEDED)
    store = GlobalContextStore(records=(active, superseded))

    assert retrieve_global_context(query(), store).records == (active,)
    assert retrieve_global_context(query(current_only=False), store).records == (active, superseded)


def test_smaller_limit_is_deterministic_and_inputs_remain_immutable():
    records = tuple(record(index, creation_sequence=index) for index in range(1, 4))
    store = GlobalContextStore(records=records)
    request = query(limit=2)

    result = retrieve_global_context(request, store)

    assert result.records == records[:2]
    assert store.records == records and request.limit == 2


def test_retrieval_has_no_ranking_or_runtime_surface():
    assert not ({"rank", "score", "relevance", "hardware", "scheduler", "runtime"}
                & set(retrieve_global_context.__annotations__))
