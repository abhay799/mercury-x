# Workload Intelligence Pipeline Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Compose the existing Phase 2 extraction, inference, and calibration contracts into one deterministic, immutable pipeline result.

**Architecture:** `mercury.intelligence.pipeline` accepts only Phase 1 `NormalizationResult` and `ConstraintNormalizationResult`, then invokes the existing Task 2, Task 3, and Task 4 entry points in order. Its result retains the stage objects by reference, checks identity at every boundary, maps calibration status directly to pipeline status, and records nonblank stage provenance.

**Tech Stack:** Python 3.13, standard-library `dataclasses` and `enum`, existing Phase 1 and Phase 2 contracts, pytest.

**Spec:** User-locked Phase 2 Task 5 request (no separate spec file is authorized).

## Global Constraints

- Create only this plan, `src/mercury/intelligence/pipeline.py`, and `tests/test_workload_intelligence_pipeline.py`.
- Reuse Task 2 signal extraction, Task 3 inference, and Task 4 calibration without duplicating their logic.
- Accept normalized Phase 1 output and canonical constraints only; never parse raw user input.
- Do not select models, providers, hardware, placement, scheduling, graphs, runtime, migration, recovery, or optimization.

---

### Task 1: Write failing pipeline integration tests

**Files:**
- Create: `tests/test_workload_intelligence_pipeline.py`

**Interfaces:**
- Consumes: Phase 1 `NormalizationResult`, `ConstraintNormalizationResult`.
- Produces: executable requirements for `analyze_workload` and immutable pipeline result composition.

- [ ] **Step 1: Define valid, degraded, and fail-closed pipeline behavior**

```python
def test_calibration_degraded_maps_to_pipeline_degraded() -> None:
    result = analyze_workload(normalization, constraints)
    assert result.status is PipelineStatus.DEGRADED
```

- [ ] **Step 2: Verify RED**

Run: `./.venv/Scripts/python.exe -m pytest tests/test_workload_intelligence_pipeline.py -q`

Expected: FAIL because `mercury.intelligence.pipeline` does not exist.

### Task 2: Compose existing Phase 2 contracts

**Files:**
- Create: `src/mercury/intelligence/pipeline.py`
- Test: `tests/test_workload_intelligence_pipeline.py`

**Interfaces:**
- Consumes: `NormalizationResult`, `ConstraintNormalizationResult`.
- Produces: `analyze_workload(normalization, constraints) -> WorkloadIntelligencePipelineResult`.

- [ ] **Step 1: Define frozen result and provenance contracts**

```python
@dataclass(frozen=True)
class WorkloadIntelligencePipelineResult:
    request_id: str
    workload_id: str
    session_id: str
    signals: WorkloadSignals | None
    profile: WorkloadIntelligenceProfile | None
    calibration: CalibratedWorkloadIntelligence | None
    status: PipelineStatus
```

- [ ] **Step 2: Invoke the three existing stage entry points in order**

Call `extract_workload_signals`, `infer_workload_intelligence`, and `calibrate_workload_intelligence`; retain their returned objects rather than copying mutable field values.

- [ ] **Step 3: Fail closed and map status exactly**

Return `FAIL` with stage provenance on extraction/inference exceptions or calibration failure; map calibration `PASS` and `DEGRADED` directly after identity consistency checks.

- [ ] **Step 4: Verify GREEN and regressions**

Run: `./.venv/Scripts/python.exe -m pytest tests/test_workload_intelligence_pipeline.py -q`

Expected: PASS.

Run once: `./.venv/Scripts/python.exe -m pytest tests -q`

Expected: PASS.
