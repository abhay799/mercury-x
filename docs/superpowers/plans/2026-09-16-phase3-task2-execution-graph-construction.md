# Execution Graph Construction Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deterministically construct an immutable logical execution DAG from a valid Phase 2 pipeline result.

**Architecture:** `mercury.graph.builder` accepts only the existing Phase 2 pipeline result and composes Task 1 graph contracts. Fixed modality, capability, complexity, and output rules append justified logical nodes in dependency order; Task 1 owns DAG validation and immutability.

**Tech Stack:** Python 3.13, existing Phase 2/Phase 3 immutable contracts, pytest.

**Spec:** User-locked Phase 3 Task 2 request (no separate spec file is authorized).

## Global Constraints

- Create only this plan, `src/mercury/graph/builder.py`, and `tests/test_execution_graph_builder.py`.
- Consume Phase 2 pipeline results only; never inspect raw gateway content.
- Reuse Task 1 graph validation without graph optimization, scheduling, runtime, resource, placement, or model decisions.
- Generate deterministic logical IDs and nonblank Phase 2-backed evidence.

---

### Task 1: Write failing graph construction tests

**Files:**
- Create: `tests/test_execution_graph_builder.py`

- [ ] **Step 1: Define deterministic modality/capability decomposition tests**

```python
def test_retrieval_capability_adds_retrieval_node() -> None:
    graph = build_execution_graph(retrieval_pipeline_result)
    assert GraphNodeType.RETRIEVAL in {node.node_type for node in graph.nodes}
```

- [ ] **Step 2: Verify RED**

Run: `./.venv/Scripts/python.exe -m pytest tests/test_execution_graph_builder.py -q`

Expected: FAIL because `mercury.graph.builder` does not exist.

### Task 2: Implement deterministic graph composition

**Files:**
- Create: `src/mercury/graph/builder.py`
- Test: `tests/test_execution_graph_builder.py`

- [ ] **Step 1: Validate Phase 2 pipeline state and identity**

- [ ] **Step 2: Generate fixed logical node/edge sequences from explicit profile signals**

- [ ] **Step 3: Construct the Task 1 immutable graph with Phase 2 provenance**

- [ ] **Step 4: Verify focused tests and full regression suite**

Run: `./.venv/Scripts/python.exe -m pytest tests/test_execution_graph_builder.py -q`

Run once: `./.venv/Scripts/python.exe -m pytest tests -q`
