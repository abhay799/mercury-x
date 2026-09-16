# Phase 4 Task 6: Integration & Failure Hardening Baseline

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stress the full Phase 4 capability lifecycle and prove unsafe, malformed, contradictory, or boundary-leaking state cannot become a valid downstream outcome.

**Architecture:** A focused integration suite creates capability records, registers them, evaluates hard compatibility, discovers compatible candidates, and assesses evidence trust. Shared fixture helpers make identity/provenance preservation and adversarial variations explicit. Production changes are forbidden except for a failing integration test that proves an existing contract invariant is missing.

**Tech Stack:** Python 3, Pydantic v2, pytest.

**Spec:** Locked Phase 4 Task 6 request, 2026-09-16.

## Global Constraints

- Create only this plan and `tests/test_model_capability_integration_failures.py`; change an existing Phase 4 production file only for a test-proven incompatibility.
- Reuse the Tasks 1–5 contracts and do not reimplement lifecycle behavior in tests.
- Do not add ranking, selection, fallback, assignment, optimization, placement, scheduling, or runtime behavior.
- Run the focused integration suite, then the full suite exactly once after focused tests pass.

---

### Task 1: Lifecycle Integration and Adversarial Coverage

**Files:**
- Create: `tests/test_model_capability_integration_failures.py`
- Create: `docs/superpowers/plans/2026-09-16-phase4-task6-integration-failure-hardening.md`
- Modify only if a failing test proves a defect: `src/mercury/models/capabilities.py`

**Interfaces:**
- Consumes: Tasks 1–5 `ModelCapabilityRecord`, registry, compatibility, discovery, and evidence assessment interfaces.
- Produces: integration evidence that valid state survives unchanged and unsafe state fails closed at the earliest applicable boundary.

- [ ] **Step 1: Write failing adversarial lifecycle tests**

```python
with pytest.raises(ValidationError, match="tool use"):
    record(supports_tool_use=False, supports_structured_tool_arguments=True)
```

Also test malformed identity/provenance, registry conflicts, incompatible discovery exclusion, current/measured/conflict evidence requirements, deterministic ordering, immutability, and absence of decision fields.

- [ ] **Step 2: Verify RED**

Run: `./.venv/Scripts/python.exe -m pytest tests/test_model_capability_integration_failures.py -q`

Expected: the contradictory structured-tool metadata test fails because the existing Task 1 contract admits the invalid combination.

- [ ] **Step 3: Apply only the proven invariant correction**

```python
@model_validator(mode="after")
def tool_metadata_requires_tool_use(self) -> ModelCapabilityRecord:
    if (self.supports_structured_tool_arguments or self.supports_tool_result_consumption) and not self.supports_tool_use:
        raise ValueError("structured tool metadata requires declared tool use support")
    return self
```

This is a compatibility fix: structured tool arguments or result consumption contradicts a record declaring no tool-use support.

- [ ] **Step 4: Verify GREEN**

Run: `./.venv/Scripts/python.exe -m pytest tests/test_model_capability_integration_failures.py -q`

Expected: all focused lifecycle and adversarial tests pass.

- [ ] **Step 5: Run regression verification**

Run: `./.venv/Scripts/python.exe -m pytest tests -q`

Expected: the complete project suite passes and only the documented proven production fix, test module, and plan have changed.
