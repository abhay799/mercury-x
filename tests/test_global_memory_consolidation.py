import pytest

from mercury.global_memory.consolidation import (
    consolidate_global_context, create_global_record_version,
)
from mercury.global_memory.contracts import (
    GlobalConsolidationRequest, GlobalMemoryConflictState, GlobalMemoryLifecycle,
    GlobalMemoryNamespace, GlobalMemoryType, GlobalContextRecord,
)


def record(identifier, **updates):
    values = dict(
        namespace_type=GlobalMemoryNamespace.PROJECT, namespace_id="project-a",
        global_record_id=f"sha256:{identifier:064d}", record_version=1,
        source_session_id="session-a", source_phase8_record_ids=("phase8-a",),
        source_artifact_ids=("artifact-a",), source_phase="phase8",
        memory_type=GlobalMemoryType.VALIDATED_FACT, context_key="context",
        creation_sequence=1, lifecycle=GlobalMemoryLifecycle.ACTIVE,
        conflict_state=GlobalMemoryConflictState.CLEAR, provenance=("evidence-a",),
        promotion_policy_id="promotion", retention_policy_id="retention",
    )
    values.update(updates)
    return GlobalContextRecord(**values)


def request(*records, **updates):
    values = dict(
        namespace_type=GlobalMemoryNamespace.PROJECT, namespace_id="project-a",
        source_record_ids=tuple(item.global_record_id for item in records),
        method_id="deterministic-summary", method_version="v1",
        context_key="summary", memory_type=GlobalMemoryType.GLOBAL_SUMMARY,
    )
    values.update(updates)
    return GlobalConsolidationRequest(**values)


def test_creates_immutable_next_global_record_version_with_explicit_lineage():
    prior = record(1)

    result = create_global_record_version(prior, change_reason="corrected evidence")

    assert result.record_version == 2
    assert result.supersedes_record_id == prior.global_record_id
    assert result.change_reason == "corrected evidence"
    assert result.namespace_type is prior.namespace_type and result.namespace_id == prior.namespace_id
    assert result.context_key == prior.context_key
    assert result.provenance == prior.provenance and result.source_phase8_record_ids == prior.source_phase8_record_ids
    assert prior.record_version == 1 and prior.supersedes_record_id is None


def test_version_creation_rejects_blank_reason_or_wrong_supersession_chain():
    prior = record(1)

    with pytest.raises(ValueError):
        create_global_record_version(prior, change_reason="")
    with pytest.raises(ValueError, match="supersedes"):
        create_global_record_version(prior, change_reason="change", supersedes_record_id="sha256:wrong")


def test_consolidates_sources_with_complete_deterministic_traceability():
    first = record(2, record_version=2, provenance=("evidence-b",), source_phase8_record_ids=("phase8-b",))
    second = record(1, record_version=1, provenance=("evidence-a",))

    result = consolidate_global_context(request(first, second), (first, second))

    assert result.record.memory_type is GlobalMemoryType.GLOBAL_SUMMARY
    assert result.record.namespace_id == "project-a" and result.record.context_key == "summary"
    assert result.source_global_record_ids == (second.global_record_id, first.global_record_id)
    assert result.source_record_versions == (1, 2)
    assert result.source_provenance == (("evidence-a",), ("evidence-b",))
    assert result.consolidation_method_id == "deterministic-summary"
    assert result.consolidation_method_version == "v1"
    assert consolidate_global_context(request(second, first), (second, first)) == result


def test_consolidation_preserves_conflicts_without_selecting_a_winner():
    clear = record(1)
    conflicting = record(2, conflict_state=GlobalMemoryConflictState.CONFLICTING,
                         provenance=("conflicting-evidence",))

    result = consolidate_global_context(request(clear, conflicting), (clear, conflicting))

    assert result.record.conflict_state is GlobalMemoryConflictState.CONFLICTING
    assert result.source_conflict_states == (
        GlobalMemoryConflictState.CLEAR, GlobalMemoryConflictState.CONFLICTING,
    )
    assert clear.provenance == ("evidence-a",) and conflicting.provenance == ("conflicting-evidence",)


def test_consolidation_rejects_cross_namespace_missing_or_duplicate_sources():
    source = record(1)
    foreign = record(2, namespace_id="project-b")

    with pytest.raises(ValueError, match="namespace"):
        consolidate_global_context(request(source, foreign), (source, foreign))
    with pytest.raises(ValueError, match="source"):
        consolidate_global_context(request(source), ())
    with pytest.raises(ValueError, match="duplicate"):
        consolidate_global_context(request(source), (source, source))


def test_consolidation_exposes_no_ranking_or_runtime_surface():
    forbidden = {"rank", "score", "winner", "hardware", "scheduler", "runtime"}
    assert not (forbidden & set(consolidate_global_context.__annotations__))
