# Execution Graph Failure and Adversarial Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove malformed, contradictory, unsafe, and boundary-violating Phase 3 graph states fail closed through construction, validation, transformation, and readiness.

**Architecture:** Exercise existing public contracts and mutate only adversarial test fixtures after construction to simulate escaped invalid states. Production changes are permitted only where a test proves an unsafe state can incorrectly become READY.

**Tech Stack:** Python 3.13, existing Phase 2/3 contracts, pytest.

**Spec:** User-locked Phase 3 Task 6 request (no separate spec file is authorized).

## Global Constraints

- Create this plan and `tests/test_execution_graph_failures.py`; change Phase 3 production only for demonstrated defects.
- Do not add graph capabilities, selection, placement, scheduling, execution, or Phase 4 behavior.
- Preserve all source artifacts during failure handling and require deterministic BLOCKED/FAIL outcomes.

---

### Task 1: Write failure-first lifecycle tests

**Files:**
- Create: `tests/test_execution_graph_failures.py`

- [ ] **Step 1: Write adversarial topology, semantic, coverage, transformation, readiness, and boundary tests**

```python
def test_stale_passing_validation_cannot_make_a_mutated_cycle_ready() -> None:
    assert evaluate_graph_readiness(mutated_graph, old_validation).status is GraphReadinessStatus.BLOCKED
```

- [ ] **Step 2: Verify RED and identify real gaps**

Run: `./.venv/Scripts/python.exe -m pytest tests/test_execution_graph_failures.py -q`

Expected: FAIL if stale validation or nested boundary leakage can bypass readiness.

### Task 2: Correct only proven readiness defects

**Files:**
- Modify only if required by RED: `src/mercury/graph/readiness.py`
- Test: `tests/test_execution_graph_failures.py`

- [ ] **Step 1: Reuse Task 3 validation for current-graph freshness and inspect nested logical artifacts for boundary leakage**

- [ ] **Step 2: Verify focused and full regression suites**

Run: `./.venv/Scripts/python.exe -m pytest tests/test_execution_graph_failures.py -q`

Run once: `./.venv/Scripts/python.exe -m pytest tests -q`
