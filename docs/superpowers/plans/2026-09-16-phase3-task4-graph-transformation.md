# Controlled Graph Transformation and Decomposition Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply deterministic, evidence-backed, validation-preserving logical graph transformations without resource or runtime decisions.

**Architecture:** `mercury.graph.transformation` requires a PASS Task 3 validation result before copying a graph. It performs bounded reasoning decomposition, justified fan-in aggregation, and safe adjacent-validation normalization, then validates the new graph again and returns frozen transformation records or a deterministic no-op.

**Tech Stack:** Python 3.13, existing Phase 2 intelligence, Phase 3 graph and validation contracts, pytest.

**Spec:** User-locked Phase 3 Task 4 request (no separate spec file is authorized).

## Global Constraints

- Create only this plan, `src/mercury/graph/transformation.py`, and `tests/test_execution_graph_transformation.py`.
- Transform only graphs that pass existing validation; never repair invalid source graphs.
- Preserve identity, logical dependency types, immutable Phase 2 provenance, and DAG validity.
- Do not select resources, scheduling, runtime, placement, precision, migration, speculative execution, or cost optimization.

---

### Task 1: Write failing transformation tests

**Files:**
- Create: `tests/test_execution_graph_transformation.py`

- [ ] **Step 1: Define precondition, bounded decomposition, aggregation, and idempotency tests**

```python
def test_invalid_graph_is_rejected_before_transformation() -> None:
    with pytest.raises(ValueError, match="validation"):
        transform_execution_graph(invalid_graph)
```

- [ ] **Step 2: Verify RED**

Run: `./.venv/Scripts/python.exe -m pytest tests/test_execution_graph_transformation.py -q`

Expected: FAIL because `mercury.graph.transformation` does not exist.

### Task 2: Implement controlled logical transformations

**Files:**
- Create: `src/mercury/graph/transformation.py`
- Test: `tests/test_execution_graph_transformation.py`

- [ ] **Step 1: Add frozen transformation result and record contracts**

- [ ] **Step 2: Gate transformations through existing validation**

- [ ] **Step 3: Apply bounded reasoning, fan-in aggregation, and safe adjacent-validation rules**

- [ ] **Step 4: Revalidate transformed graphs and verify idempotency**

Run: `./.venv/Scripts/python.exe -m pytest tests/test_execution_graph_transformation.py -q`

Run once: `./.venv/Scripts/python.exe -m pytest tests -q`
