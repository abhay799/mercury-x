# Workload Intelligence Failure and Edge-Case Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove the complete Phase 2 intelligence pipeline rejects malformed, contradictory, unsafe, and boundary-leaking states.

**Architecture:** Exercise the existing immutable Task 1–5 contracts through their public construction, calibration, and pipeline interfaces. Add production code only if a focused contradiction test demonstrates that an unsafe profile currently passes calibration.

**Tech Stack:** Python 3.13, existing Phase 1/Phase 2 contracts, pytest.

**Spec:** User-locked Phase 2 Task 6 request (no separate spec file is authorized).

## Global Constraints

- Create this plan and `tests/test_workload_intelligence_failures.py`; modify Phase 2 production only for a demonstrated defect.
- Do not alter Phase 0 or Phase 1, add categories, selection, placement, scheduling, graphs, or runtime behavior.
- Keep failure outputs deterministic, immutable, and free of concrete resource fields.

---

### Task 1: Write failure-first cross-stage tests

**Files:**
- Create: `tests/test_workload_intelligence_failures.py`

- [ ] **Step 1: Write contradiction and malformed-state tests**

```python
def test_visual_capability_without_visual_signal_fails_closed() -> None:
    result = calibrate_workload_intelligence(text_signals, visual_profile)
    assert result.status is CalibrationStatus.FAIL
```

- [ ] **Step 2: Verify RED**

Run: `./.venv/Scripts/python.exe -m pytest tests/test_workload_intelligence_failures.py -q`

Expected: FAIL if an unsupported capability is not detected.

### Task 2: Correct only demonstrated calibration gaps

**Files:**
- Modify only if RED proves a defect: `src/mercury/intelligence/calibration.py`
- Test: `tests/test_workload_intelligence_failures.py`

- [ ] **Step 1: Add the smallest signal/capability contradiction checks required by RED**

- [ ] **Step 2: Verify focused tests and full regression suite**

Run: `./.venv/Scripts/python.exe -m pytest tests/test_workload_intelligence_failures.py -q`

Run once: `./.venv/Scripts/python.exe -m pytest tests -q`
