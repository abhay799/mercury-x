# Graph Execution Readiness and Invariant Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Determine whether a validated logical execution graph is READY to leave Phase 3 without compiling, scheduling, executing, or selecting concrete resources.

**Architecture:** `mercury.graph.readiness` consumes a graph, its Task 3 validation result, and optional Task 4 transformation result. It checks cross-artifact identity, validation status, provenance, transformation consistency, and boundary leakage, then returns frozen deterministic invariant evidence and BLOCKED issues.

**Tech Stack:** Python 3.13, existing Phase 2/3 immutable contracts, pytest.

**Spec:** User-locked Phase 3 Task 5 request (no separate spec file is authorized).

## Global Constraints

- Create only this plan, `src/mercury/graph/readiness.py`, and `tests/test_execution_graph_readiness.py`.
- Reuse Task 3 validation; do not rebuild, transform, repair, compile, schedule, or execute graphs.
- Block on mandatory invariant failures and physical-execution leakage.
- Emit logical readiness information only; no model, provider, hardware, placement, scheduler, runtime, precision, migration, speculative, or cost decisions.

---

### Task 1: Write failing readiness tests

**Files:**
- Create: `tests/test_execution_graph_readiness.py`

- [ ] **Step 1: Define READY and BLOCKED invariant behavior**

```python
def test_failed_validation_blocks_readiness() -> None:
    result = evaluate_graph_readiness(graph, failed_validation)
    assert result.status is GraphReadinessStatus.BLOCKED
```

- [ ] **Step 2: Verify RED**

Run: `./.venv/Scripts/python.exe -m pytest tests/test_execution_graph_readiness.py -q`

Expected: FAIL because `mercury.graph.readiness` does not exist.

### Task 2: Implement immutable readiness gating

**Files:**
- Create: `src/mercury/graph/readiness.py`
- Test: `tests/test_execution_graph_readiness.py`

- [ ] **Step 1: Add frozen status, issue, evidence, and result contracts**

- [ ] **Step 2: Check supplied validation, identity, transformation, provenance, and boundary invariants**

- [ ] **Step 3: Return sorted deterministic evidence and issues without source mutation**

- [ ] **Step 4: Verify focused tests and full regression suite**

Run: `./.venv/Scripts/python.exe -m pytest tests/test_execution_graph_readiness.py -q`

Run once: `./.venv/Scripts/python.exe -m pytest tests -q`
