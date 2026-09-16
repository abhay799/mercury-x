# Execution Graph Contract Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Define immutable, validated logical execution-graph contracts that decompose a workload without selecting concrete execution resources.

**Architecture:** Add frozen logical graph dataclasses beside the existing legacy graph API. New nodes and edges use Phase 2 `ComputationalCapability` and `Evidence` contracts, sort set-like collections deterministically, and validate identity, references, and DAG safety at graph construction.

**Tech Stack:** Python 3.13, standard-library dataclasses/enums, existing Phase 2 contracts, pytest.

**Spec:** User-locked Phase 3 Task 1 request (no separate spec file is authorized).

## Global Constraints

- Create only this plan, `src/mercury/graph/models.py`, and `tests/test_execution_graph_models.py`.
- Preserve legacy `AIExecutionGraph` behavior.
- Define logical relationships only; expose no model, provider, hardware, region, placement, scheduler, graph-runtime, migration, or speculative fields.
- Do not construct, optimize, schedule, or execute graphs.

---

### Task 1: Define failing logical graph contract tests

**Files:**
- Create: `tests/test_execution_graph_models.py`

- [ ] **Step 1: Write immutable DAG validation tests**

```python
def test_cycle_is_rejected() -> None:
    with pytest.raises(ValueError, match="cycle"):
        ExecutionGraph(...)
```

- [ ] **Step 2: Verify RED**

Run: `./.venv/Scripts/python.exe -m pytest tests/test_execution_graph_models.py -q`

Expected: FAIL because the new logical graph contracts do not exist.

### Task 2: Add frozen logical graph contracts

**Files:**
- Modify: `src/mercury/graph/models.py`
- Test: `tests/test_execution_graph_models.py`

- [ ] **Step 1: Add node, edge, graph status, and logical enum contracts**

- [ ] **Step 2: Validate nonblank identity/provenance, unique nodes, dangling/self edges, and cycles**

- [ ] **Step 3: Normalize graph collections and preserve compatible Phase 2 profile provenance**

- [ ] **Step 4: Verify focused tests and full regression suite**

Run: `./.venv/Scripts/python.exe -m pytest tests/test_execution_graph_models.py -q`

Run once: `./.venv/Scripts/python.exe -m pytest tests -q`
