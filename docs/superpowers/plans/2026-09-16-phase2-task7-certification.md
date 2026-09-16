# Phase 2 Certification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Certify the complete Phase 2 Workload Intelligence Engine with 13 machine-readable, fail-closed gates.

**Architecture:** Follow the existing Phase 0/1 frozen Pydantic certification-contract pattern. A configuration contains unique immutable gate records and known boundary violations; evaluation determines missing coverage, pass/fail counts, and the overall result without reimplementing Phase 2 runtime behavior.

**Tech Stack:** Python 3.13, Pydantic contracts, JSON configuration, pytest.

**Spec:** User-locked Phase 2 Task 7 request (no separate spec file is authorized).

## Global Constraints

- Create only this plan, `src/mercury/certification/phase2.py`, `configs/certification/phase2.json`, and `tests/test_phase2_certification.py`.
- Require all 13 locked gate IDs and nonblank evidence.
- Fail closed on incomplete coverage, failures, duplicates, malformed configuration, and any resource-selection boundary violation.
- Certify intelligence characteristics only; never certify model, provider, hardware, placement, scheduler, graph, runtime, migration, or optimization selection.

---

### Task 1: Write failing Phase 2 certification tests

**Files:**
- Create: `tests/test_phase2_certification.py`

- [ ] **Step 1: Specify complete-pass and fail-closed gate behavior**

```python
def test_model_selection_boundary_violation_forces_failure() -> None:
    result = evaluate_phase2_certification(config_with("model_selection"))
    assert result.overall_passed is False
```

- [ ] **Step 2: Verify RED**

Run: `./.venv/Scripts/python.exe -m pytest tests/test_phase2_certification.py -q`

Expected: FAIL because `mercury.certification.phase2` does not exist.

### Task 2: Implement certification contracts and checklist

**Files:**
- Create: `src/mercury/certification/phase2.py`
- Create: `configs/certification/phase2.json`
- Test: `tests/test_phase2_certification.py`

- [ ] **Step 1: Add frozen gate, config, and result contracts**

- [ ] **Step 2: Evaluate complete required coverage and known boundary violations**

- [ ] **Step 3: Add the 13-gate machine-readable certification configuration**

- [ ] **Step 4: Verify focused tests, full regression, and the loaded Phase 2 certification result**

Run: `./.venv/Scripts/python.exe -m pytest tests/test_phase2_certification.py -q`

Run once: `./.venv/Scripts/python.exe -m pytest tests -q`
