# Workload Intelligence Analysis Contract Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Provide immutable, validated workload-intelligence analysis contracts without selecting or executing any infrastructure.

**Architecture:** Define a dependency-free `mercury.intelligence.models` module of frozen value objects and string enums. `WorkloadIntelligenceProfile` is the analysis boundary: it accepts request identity and capability needs, canonicalizes enum collections into sorted tuples, validates explainability evidence, and serializes to deterministic primitive data only.

**Tech Stack:** Python 3.13, standard-library `dataclasses` and `enum`, pytest.

**Spec:** User-locked Phase 2 Task 1 request (no separate spec file is authorized).

## Global Constraints

- Create only this plan, `src/mercury/intelligence/models.py`, and `tests/test_workload_intelligence_models.py`.
- Do not modify certified Phase 0 or Phase 1 modules.
- Do not implement inference, classification, selection, placement, scheduling, execution graphs, or runtime execution.
- Do not expose model, provider, hardware, device, region, placement, scheduler, execution-graph, or runtime-execution fields.

---

### Task 1: Workload intelligence contract tests

**Files:**
- Create: `tests/test_workload_intelligence_models.py`

**Interfaces:**
- Consumes: `mercury.intelligence.models` public enums and frozen dataclasses.
- Produces: behavioral contract coverage for valid profiles, validation failures, normalization, serialization, and prohibited fields.

- [ ] **Step 1: Write the failing tests**

```python
def test_profile_normalizes_collections_and_serializes_deterministically() -> None:
    profile = WorkloadIntelligenceProfile(...)
    assert profile.modalities == (WorkloadModality.IMAGE, WorkloadModality.TEXT)
    assert profile.to_dict()["modalities"] == ["image", "text"]
```

- [ ] **Step 2: Run the focused test file to verify it fails**

Run: `..venv\Scripts\python.exe -m pytest tests/test_workload_intelligence_models.py -q`

Expected: FAIL because `mercury.intelligence.models` does not exist.

### Task 2: Frozen analysis contracts

**Files:**
- Create: `src/mercury/intelligence/models.py`
- Test: `tests/test_workload_intelligence_models.py`

**Interfaces:**
- Consumes: primitive strings, enum members, and iterable collections supplied by analysis callers.
- Produces: `WorkloadIntelligenceProfile.to_dict() -> dict[str, object]` with deterministic primitive values.

- [ ] **Step 1: Implement the smallest frozen value-object API**

```python
@dataclass(frozen=True)
class WorkloadIntelligenceProfile:
    request_id: str
    workload_id: str
    session_id: str
    modalities: tuple[WorkloadModality, ...]
    # remaining validated requirements

    def to_dict(self) -> dict[str, object]:
        ...
```

- [ ] **Step 2: Validate boundaries in `__post_init__`**

Reject blank identity/evidence values, confidence outside `[0.0, 1.0]`, empty semantically-required collections, and inconsistent tool/context requirements. Convert modality and capability iterables to sorted, duplicate-free tuples.

- [ ] **Step 3: Run focused tests to verify the implementation**

Run: `..venv\Scripts\python.exe -m pytest tests/test_workload_intelligence_models.py -q`

Expected: PASS.

- [ ] **Step 4: Run the complete suite once**

Run: `..venv\Scripts\python.exe -m pytest tests -q`

Expected: PASS with the prior regression baseline plus the new focused tests.
