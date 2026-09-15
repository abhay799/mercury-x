from pathlib import Path

import pytest

from mercury.benchmark import BenchmarkCatalog, BenchmarkDefinition, load_benchmark_catalog


CATALOG_PATH = Path("configs/benchmarks/workloads.json")
REQUIRED_CATEGORIES = {
    "text_generation_small",
    "text_generation_large",
    "embedding",
    "rag",
    "classification",
    "batch",
    "latency_critical",
    "long_context",
    "agent_tool",
    "multi_model_dag",
}


def test_catalog_covers_required_mercury_workload_classes():
    catalog = load_benchmark_catalog(CATALOG_PATH)
    assert {item.category for item in catalog.definitions} == REQUIRED_CATEGORIES


def test_every_benchmark_keeps_request_and_profile_identity_consistent():
    catalog = load_benchmark_catalog(CATALOG_PATH)
    for item in catalog.definitions:
        assert item.request.workload_id == item.profile.workload_id


def test_every_definition_is_cpu_safe_and_gpu_is_remote_only_when_enabled():
    catalog = load_benchmark_catalog(CATALOG_PATH)
    for item in catalog.definitions:
        assert "LOCAL_CPU" in item.allowed_execution_modes
        assert "LOCAL_GPU" not in item.allowed_execution_modes
    assert any("REMOTE_GPU" in item.allowed_execution_modes for item in catalog.definitions)


def test_latency_critical_workload_has_explicit_tight_latency_intent():
    catalog = load_benchmark_catalog(CATALOG_PATH)
    item = catalog.get("bench-latency-critical-v1")
    assert item.profile.latency_sensitive is True
    assert item.request.latency_target_ms <= 500


def test_long_context_and_agent_benchmarks_exercise_required_features():
    catalog = load_benchmark_catalog(CATALOG_PATH)
    long_context = catalog.get("bench-long-context-v1")
    agent = catalog.get("bench-agent-tool-v1")
    assert long_context.profile.context_bytes >= 1_000_000
    assert agent.profile.required_tools


def test_multi_model_dag_benchmark_requires_multiple_capability_classes():
    catalog = load_benchmark_catalog(CATALOG_PATH)
    item = catalog.get("bench-multi-model-dag-v1")
    assert len(item.profile.required_capabilities) >= 3


def test_catalog_rejects_duplicate_ids_and_definitions_do_not_store_results():
    catalog = load_benchmark_catalog(CATALOG_PATH)
    first = catalog.definitions[0]
    with pytest.raises(ValueError, match="duplicate benchmark_id"):
        BenchmarkCatalog(definitions=[first, first])
    assert "result" not in BenchmarkDefinition.model_fields
    assert "measured_latency_ms" not in BenchmarkDefinition.model_fields
    assert all(item.evidence_state == "DEFINITION_ONLY" for item in catalog.definitions)
