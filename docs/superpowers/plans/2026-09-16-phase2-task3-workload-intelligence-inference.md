# Workload Intelligence Inference Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deterministically convert Task 2 observable signals into the immutable Task 1 workload-intelligence profile.

**Architecture:** `mercury.intelligence.inference` consumes `WorkloadSignals` exclusively. It maps explicit signal fields and canonical constraint values through documented threshold tables, records one evidence item per inferred profile concern, and rejects missing identity or modality evidence rather than reading request content or selecting execution resources.

**Tech Stack:** Python 3.13, standard-library functions, Task 1/Task 2 immutable contracts, pytest.

**Spec:** User-locked Phase 2 Task 3 request (no separate spec file is authorized).

## Global Constraints

- Create only this plan, `src/mercury/intelligence/inference.py`, and `tests/test_workload_intelligence_inference.py`.
- Use only `WorkloadSignals`; do not read gateway requests or alter prior phases/tasks.
- Do not select models, providers, hardware, devices, regions, placement, schedules, graphs, runtime, migration, or optimization.
- Fail closed when identity or final modality evidence is absent or malformed.

---

### Task 1: Specify inference mappings with failing tests

**Files:**
- Create: `tests/test_workload_intelligence_inference.py`

**Interfaces:**
- Consumes: `WorkloadSignals` created by Task 2.
- Produces: executable requirements for `infer_workload_intelligence(signals)`.

- [ ] **Step 1: Write failing mapping and boundary tests**

```python
def test_image_signal_maps_to_image_modality_and_vision_capability() -> None:
    profile = infer_workload_intelligence(signals(input={"images": ["image-1"]}))
    assert profile.modalities == (WorkloadModality.IMAGE,)
    assert ComputationalCapability.VISION in profile.required_capabilities
```

- [ ] **Step 2: Verify RED**

Run: `./.venv/Scripts/python.exe -m pytest tests/test_workload_intelligence_inference.py -q`

Expected: FAIL because `mercury.intelligence.inference` does not exist.

### Task 2: Implement deterministic intelligence inference

**Files:**
- Create: `src/mercury/intelligence/inference.py`
- Test: `tests/test_workload_intelligence_inference.py`

**Interfaces:**
- Consumes: `WorkloadSignals`.
- Produces: `infer_workload_intelligence(signals: WorkloadSignals) -> WorkloadIntelligenceProfile`.

- [ ] **Step 1: Add explicit mapping tables and fail-closed validation**

```python
def infer_workload_intelligence(signals: WorkloadSignals) -> WorkloadIntelligenceProfile:
    if not signals.explicit_modalities:
        raise ValueError("modality evidence is required")
    ...
```

- [ ] **Step 2: Map constraints and explicit capabilities**

Map latency thresholds, quality scores, exact privacy values, context/tool/output indicators, and only evidence-supported capability values. Preserve Task 2 immutability.

- [ ] **Step 3: Emit profile evidence and bounded deterministic confidence**

Every profile concern receives nonblank `Evidence`; confidence is a reproducible bounded score that increases only with additional explicit signal groups.

- [ ] **Step 4: Verify GREEN and regressions**

Run: `./.venv/Scripts/python.exe -m pytest tests/test_workload_intelligence_inference.py -q`

Expected: PASS.

Run once: `./.venv/Scripts/python.exe -m pytest tests -q`

Expected: PASS.
