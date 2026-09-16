# Workload Signal Extraction Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract deterministic, immutable, evidence-backed observable signals from a normalized gateway request and canonical constraints.

**Architecture:** `mercury.intelligence.signals` is a read-only boundary over Phase 1 `NormalizationResult` and `ConstraintNormalizationResult`. It recognizes only exact input/context metadata keys and copies relevant canonical constraints without reinterpreting them; absent values remain `None` or empty immutable tuples.

**Tech Stack:** Python 3.13, standard-library `dataclasses`, existing Pydantic Phase 1 contracts, pytest.

**Spec:** User-locked Phase 2 Task 2 request (no separate spec file is authorized).

## Global Constraints

- Create only this plan, `src/mercury/intelligence/signals.py`, and `tests/test_workload_signal_extraction.py`.
- Do not modify Phase 0, Phase 1, or Phase 2 Task 1 contracts.
- Do not infer modalities, reasoning, quality, privacy, models, hardware, placement, scheduling, graphs, or execution.
- Use only explicit normalized request fields and `LATENCY`, `QUALITY`, `PRIVACY`, and `COST` canonical constraints.

---

### Task 1: Define the extraction behavior with failing tests

**Files:**
- Create: `tests/test_workload_signal_extraction.py`

**Interfaces:**
- Consumes: Phase 1 `NormalizationResult` and `ConstraintNormalizationResult`.
- Produces: executable requirements for `extract_workload_signals` and `WorkloadSignals`.

- [ ] **Step 1: Write focused contract tests**

```python
def test_text_signal_is_extracted_only_from_an_explicit_input_key() -> None:
    signals = extract_workload_signals(normalized({"text": "hello"}), constraints)
    assert signals.text_input_present is True
    assert signals.text_character_count == 5
```

- [ ] **Step 2: Verify RED**

Run: `./.venv/Scripts/python.exe -m pytest tests/test_workload_signal_extraction.py -q`

Expected: FAIL because `mercury.intelligence.signals` does not exist.

### Task 2: Implement immutable observable signals

**Files:**
- Create: `src/mercury/intelligence/signals.py`
- Test: `tests/test_workload_signal_extraction.py`

**Interfaces:**
- Consumes: `NormalizationResult`, `ConstraintNormalizationResult`.
- Produces: `extract_workload_signals(normalization, constraints) -> WorkloadSignals`.

- [ ] **Step 1: Add frozen signal and evidence value objects**

```python
@dataclass(frozen=True)
class WorkloadSignals:
    request_id: str
    workload_id: str
    session_id: str
    evidence: tuple[SignalEvidence, ...]
```

- [ ] **Step 2: Fail closed before extraction**

Reject incomplete normalization, incomplete canonicalization, blank identities, and mismatched identity triples. Never mutate either Phase 1 input object.

- [ ] **Step 3: Extract exact-key request/context/output/tool signals and canonical constraints**

Use only documented exact mapping keys; normalize set-like strings into sorted tuples; derive character counts only from explicit text strings; preserve canonical constraint objects unchanged.

- [ ] **Step 4: Verify GREEN and regressions**

Run: `./.venv/Scripts/python.exe -m pytest tests/test_workload_signal_extraction.py -q`

Expected: PASS.

Run once: `./.venv/Scripts/python.exe -m pytest tests -q`

Expected: PASS.
