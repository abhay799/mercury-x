# Confidence and Evidence Calibration Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Validate and conservatively calibrate Task 3 profile confidence against Task 2 observable signals while preserving the original profile.

**Architecture:** `mercury.intelligence.calibration` accepts immutable signals and profile contracts, validates identity, provenance, conservative fallbacks, and signal/profile consistency, then returns a frozen result containing the unchanged profile, a non-inflated confidence, status, and field-level decisions. It uses fixed evidence-strength and confidence-ceiling rules only.

**Tech Stack:** Python 3.13, standard-library `dataclasses` and `enum`, existing Phase 2 contracts, pytest.

**Spec:** User-locked Phase 2 Task 4 request (no separate spec file is authorized).

## Global Constraints

- Create only this plan, `src/mercury/intelligence/calibration.py`, and `tests/test_workload_intelligence_calibration.py`.
- Do not modify Phase 0, Phase 1, or Phase 2 Tasks 1–3.
- Do not use probabilistic ML, LLM scoring, new categories, selection, placement, scheduling, graphs, or runtime execution.
- Preserve the input profile and expose calibration only as explicit metadata.

---

### Task 1: Specify calibration behavior with failing tests

**Files:**
- Create: `tests/test_workload_intelligence_calibration.py`

**Interfaces:**
- Consumes: `WorkloadSignals`, `WorkloadIntelligenceProfile`.
- Produces: executable requirements for `calibrate_workload_intelligence`.

- [ ] **Step 1: Write failing consistency, confidence, and boundary tests**

```python
def test_text_signal_and_image_profile_fail_calibration() -> None:
    result = calibrate_workload_intelligence(text_signals, image_profile)
    assert result.status is CalibrationStatus.FAIL
```

- [ ] **Step 2: Verify RED**

Run: `./.venv/Scripts/python.exe -m pytest tests/test_workload_intelligence_calibration.py -q`

Expected: FAIL because `mercury.intelligence.calibration` does not exist.

### Task 2: Implement immutable calibration

**Files:**
- Create: `src/mercury/intelligence/calibration.py`
- Test: `tests/test_workload_intelligence_calibration.py`

**Interfaces:**
- Consumes: `WorkloadSignals`, `WorkloadIntelligenceProfile`.
- Produces: `calibrate_workload_intelligence(signals, profile) -> CalibratedWorkloadIntelligence`.

- [ ] **Step 1: Define frozen result, decision, strength, severity, and status contracts**

```python
class CalibrationStatus(str, Enum):
    PASS = "pass"
    DEGRADED = "degraded"
    FAIL = "fail"
```

- [ ] **Step 2: Validate evidence and detect contradictions**

Verify each profile concern has nonblank provenance; report mismatched identity, modality, tool, retrieval, structured-output, and unsafe fallback conflicts as explicit non-PASS decisions.

- [ ] **Step 3: Apply the deterministic non-inflation ceiling**

Start from a ceiling of `1.00`, subtract `0.10` per defaulted field and `0.03` per derived field, cap calibrated confidence by the original profile confidence, and set confidence to `0.00` on FAIL.

- [ ] **Step 4: Verify GREEN and regressions**

Run: `./.venv/Scripts/python.exe -m pytest tests/test_workload_intelligence_calibration.py -q`

Expected: PASS.

Run once: `./.venv/Scripts/python.exe -m pytest tests -q`

Expected: PASS.
