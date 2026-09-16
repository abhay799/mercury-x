# Phase 3 Certification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Certify the complete logical AI Execution Graph baseline with 15 machine-readable, fail-closed gates.

**Architecture:** Follow the existing frozen Phase 0–2 certification contract pattern. A Phase 3 configuration holds unique gate records and known direct/nested logical-boundary violations; evaluation reports required coverage, pass/fail counts, missing gates, and boundary violations without graph mutation or runtime behavior.

**Tech Stack:** Python 3.13, Pydantic immutable contracts, JSON configuration, pytest.

**Spec:** User-locked Phase 3 Task 7 request (no separate spec file is authorized).

## Global Constraints

- Create only this plan, `src/mercury/certification/phase3.py`, `configs/certification/phase3.json`, and `tests/test_phase3_certification.py`.
- Require all 15 locked gates, unique IDs, and nonblank deterministic evidence.
- Fail closed on missing/failed coverage and all direct or nested concrete-resource boundary violations.
- Certify logical graph behavior only; do not encode model, provider, hardware, placement, scheduler, runtime, precision, migration, speculative, or optimization decisions.

---

### Task 1: Write failing Phase 3 certification tests

**Files:**
- Create: `tests/test_phase3_certification.py`

- [ ] **Step 1: Define complete-pass and fail-closed coverage/boundary tests**

```python
def test_nested_boundary_leakage_forces_fail() -> None:
    assert evaluate_phase3_certification(config_with("nested_boundary_leakage")).overall_passed is False
```

- [ ] **Step 2: Verify RED**

Run: `./.venv/Scripts/python.exe -m pytest tests/test_phase3_certification.py -q`

Expected: FAIL because `mercury.certification.phase3` does not exist.

### Task 2: Implement the 15-gate certification contracts

**Files:**
- Create: `src/mercury/certification/phase3.py`
- Create: `configs/certification/phase3.json`
- Test: `tests/test_phase3_certification.py`

- [ ] **Step 1: Add frozen gate, config, and result contracts**

- [ ] **Step 2: Evaluate complete required coverage and direct/nested boundary violations**

- [ ] **Step 3: Add checked-in 15-gate machine-readable configuration**

- [ ] **Step 4: Verify focused tests, full regression, and certification evaluation**

Run: `./.venv/Scripts/python.exe -m pytest tests/test_phase3_certification.py -q`

Run once: `./.venv/Scripts/python.exe -m pytest tests -q`
