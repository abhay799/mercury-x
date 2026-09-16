# Graph Dependency and Data-Flow Validation Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Validate logical execution-graph reachability, dependency semantics, data flow, capability coverage, and deterministic topology without rewriting the graph.

**Architecture:** `mercury.graph.validation` consumes a frozen Task 1 graph and emits a frozen result with sorted issues and a topological representation. It reuses Task 1 structural contracts, analyzes all valid directed edges read-only, and maps any semantic safety violation to FAIL.

**Tech Stack:** Python 3.13, standard-library dataclasses/enums, existing Phase 2 capabilities and Phase 3 graph contracts, pytest.

**Spec:** User-locked Phase 3 Task 3 request (no separate spec file is authorized).

## Global Constraints

- Create only this plan, `src/mercury/graph/validation.py`, and `tests/test_execution_graph_validation.py` unless a test proves a Task 1/2 defect.
- Do not construct, optimize, reorder, delete, schedule, execute, or assign resources to graphs.
- Return deterministic logical validation findings only; no model, provider, hardware, placement, scheduler, runtime, migration, precision, or cost fields.

---

### Task 1: Write failing semantic flow tests

**Files:**
- Create: `tests/test_execution_graph_validation.py`

- [ ] **Step 1: Define valid flow and fail-closed dependency tests**

```python
def test_tool_result_from_non_tool_source_fails() -> None:
    result = validate_execution_graph(graph)
    assert result.status is GraphValidationStatus.FAIL
```

- [ ] **Step 2: Verify RED**

Run: `./.venv/Scripts/python.exe -m pytest tests/test_execution_graph_validation.py -q`

Expected: FAIL because `mercury.graph.validation` does not exist.

### Task 2: Implement immutable semantic validation

**Files:**
- Create: `src/mercury/graph/validation.py`
- Test: `tests/test_execution_graph_validation.py`

- [ ] **Step 1: Add frozen result and issue contracts**

- [ ] **Step 2: Analyze reachability, entry/exit, dependency, data-flow, and coverage rules**

- [ ] **Step 3: Compute sorted deterministic topological representation without mutation**

- [ ] **Step 4: Verify focused tests and full regression suite**

Run: `./.venv/Scripts/python.exe -m pytest tests/test_execution_graph_validation.py -q`

Run once: `./.venv/Scripts/python.exe -m pytest tests -q`
