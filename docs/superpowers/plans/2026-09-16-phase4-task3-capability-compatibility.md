# Phase 4 Task 3: Capability Compatibility & Constraint Evaluation Baseline

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deterministically decide whether one declared `ModelCapabilityRecord` satisfies an explicit set of logical hard constraints, without comparing or selecting models.

**Architecture:** A frozen `ModelCapabilityRequirements` contract contains only explicit modality, reasoning, boolean capability, token-limit, streaming, lifecycle, and evidence requirements. `evaluate_compatibility` checks those fields against one Task 1 record and returns a frozen `CompatibilityResult` with canonical, evidence-backed incompatibility issues.

**Tech Stack:** Python 3, Pydantic v2, pytest.

**Spec:** Locked Phase 4 Task 3 request, 2026-09-16.

## Global Constraints

- Create only this plan, `src/mercury/models/compatibility.py`, and `tests/test_model_capability_compatibility.py`.
- Reuse Phase 4 Tasks 1 and 2 contracts without changing them.
- Evaluate hard compatibility of exactly one record at a time.
- Do not score, rank, compare, select, route, place, schedule, or execute models.
- Treat unknown declared limits as incompatible when a matching hard minimum is required.

---

### Task 1: Immutable Hard Compatibility Evaluation

**Files:**
- Create: `src/mercury/models/compatibility.py`
- Test: `tests/test_model_capability_compatibility.py`

**Interfaces:**
- Consumes: `ModelCapabilityRecord`, `ModelModality`, `ReasoningCapability`, and `CapabilityStatus` from `mercury.models.capabilities`.
- Produces: `ModelCapabilityRequirements`, `CompatibilityIssue`, `CompatibilityStatus`, `CompatibilityResult`, and `evaluate_compatibility(record, requirements)`.

- [ ] **Step 1: Write failing compatibility tests**

```python
result = evaluate_compatibility(
    model(),
    ModelCapabilityRequirements(
        required_input_modalities=(ModelModality.TEXT,),
        minimum_context_tokens=4096,
        evidence=("logical graph requirement",),
    ),
)
assert result.status is CompatibilityStatus.COMPATIBLE
```

- [ ] **Step 2: Verify RED**

Run: `./.venv/Scripts/python.exe -m pytest tests/test_model_capability_compatibility.py -q`

Expected: collection fails because `mercury.models.compatibility` does not exist.

- [ ] **Step 3: Implement exact hard-constraint evaluation**

```python
def evaluate_compatibility(
    record: ModelCapabilityRecord,
    requirements: ModelCapabilityRequirements,
) -> CompatibilityResult:
    ...
```

Reject malformed requirements, require nonblank evidence, normalize tuple constraints deterministically, and generate stable issues for unsupported modalities/reasoning/declared features, unknown or insufficient limits, and disallowed lifecycle statuses. Return `COMPATIBLE` only when no hard issue exists.

- [ ] **Step 4: Verify GREEN**

Run: `./.venv/Scripts/python.exe -m pytest tests/test_model_capability_compatibility.py -q`

Expected: all focused compatibility tests pass.

- [ ] **Step 5: Run regression verification**

Run: `./.venv/Scripts/python.exe -m pytest tests -q`

Expected: the complete project suite passes with no changes outside Task 3.
