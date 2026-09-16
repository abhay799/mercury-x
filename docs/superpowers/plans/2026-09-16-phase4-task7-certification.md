# Phase 4 Certification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Certify the complete Model Capability Fabric baseline with 14 machine-readable, fail-closed gates.

**Architecture:** Follow the frozen Phase 3 certification pattern. A Phase 4 configuration contains unique, canonical gate records plus known lifecycle and boundary violations; evaluation reports required coverage, pass/fail counts, missing gates, and violations without changing any Phase 4 artifact or making model decisions.

**Tech Stack:** Python 3, Pydantic immutable contracts, JSON configuration, pytest.

**Spec:** User-locked Phase 4 Task 7 request (no separate specification file is authorized).

## Global Constraints

- Create only this plan, `src/mercury/certification/phase4.py`, `configs/certification/phase4.json`, and `tests/test_phase4_certification.py`.
- Require all 14 locked gates, unique known IDs, nonblank deterministic evidence, and no unresolved lifecycle or boundary violations.
- Fail closed on identity, provenance, status, determinism, registry, compatibility, discovery, or evidence defects.
- Certify capability description and hard evaluation only; do not rank, score preference, select, assign, optimize, place, schedule, or invoke models.

---

### Task 1: Write failing Phase 4 certification tests

**Files:**
- Create: `tests/test_phase4_certification.py`

**Interfaces:**
- Consumes: the locked 14 gate identifiers and checked-in JSON certification configuration.
- Produces: focused proof for complete PASS, missing/failed gates, malformed configuration, lifecycle violations, boundary leakage, determinism, and immutability.

- [ ] **Step 1: Define complete-pass and fail-closed tests**

```python
result = evaluate_phase4_certification(complete_config())
assert result.overall_passed is True
assert (result.passed_gate_count, result.failed_gate_count) == (14, 0)
```

- [ ] **Step 2: Verify RED**

Run: `./.venv/Scripts/python.exe -m pytest tests/test_phase4_certification.py -q`

Expected: collection fails because `mercury.certification.phase4` does not exist.

### Task 2: Implement the 14-gate certification baseline

**Files:**
- Create: `src/mercury/certification/phase4.py`
- Create: `configs/certification/phase4.json`
- Test: `tests/test_phase4_certification.py`

**Interfaces:**
- Produces: `Phase4Gate`, `Phase4CertificationConfig`, `Phase4CertificationResult`, and `evaluate_phase4_certification(config)`.

- [ ] **Step 1: Add frozen gate, config, and result contracts**

```python
class Phase4CertificationConfig(ContractModel):
    schema_version: Literal["mercury.certification.phase4/v1"]
    gates: tuple[Phase4Gate, ...]
    certification_violations: tuple[str, ...] = ()
    boundary_violations: tuple[str, ...] = ()
```

- [ ] **Step 2: Evaluate exact required coverage and known violations**

```python
overall_passed = (
    not missing_gate_ids
    and not failed_gate_count
    and not config.certification_violations
    and not config.boundary_violations
)
```

- [ ] **Step 3: Add the checked-in 14-gate configuration**

Every required gate is present once with `passed: true` and nonblank repository evidence; both violation collections are empty.

- [ ] **Step 4: Verify focused tests, full regression, and certification evaluation**

Run: `./.venv/Scripts/python.exe -m pytest tests/test_phase4_certification.py -q`

Run once: `./.venv/Scripts/python.exe -m pytest tests -q`

Evaluate: load `configs/certification/phase4.json`, validate it as `Phase4CertificationConfig`, and run `evaluate_phase4_certification`.
