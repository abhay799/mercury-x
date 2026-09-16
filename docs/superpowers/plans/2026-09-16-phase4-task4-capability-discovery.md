# Phase 4 Task 4: Capability Query & Candidate Discovery Baseline

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Return every registered model capability record that satisfies one explicit hard requirement set, without ranking or selecting candidates.

**Architecture:** A frozen discovery query composes the Task 2 registry and Task 3 requirements. Discovery delegates each record evaluation to `evaluate_compatibility`, retains only `COMPATIBLE` results, and exposes frozen candidates containing the unchanged record plus exact compatibility evidence in canonical identity order.

**Tech Stack:** Python 3, Pydantic v2, pytest.

**Spec:** Locked Phase 4 Task 4 request, 2026-09-16.

## Global Constraints

- Create only this plan, `src/mercury/models/discovery.py`, and `tests/test_model_capability_discovery.py`.
- Reuse Tasks 1–3 without duplicating registry or compatibility behavior.
- Return every compatible candidate or a valid empty collection; never relax hard requirements.
- Canonical candidate ordering is reproducibility-only and has no preference semantics.
- Do not score, rank, select, assign, route, place, schedule, or execute models.

---

### Task 1: Immutable Candidate Discovery

**Files:**
- Create: `src/mercury/models/discovery.py`
- Test: `tests/test_model_capability_discovery.py`

**Interfaces:**
- Consumes: `ModelCapabilityRegistry`, `ModelCapabilityRequirements`, `CompatibilityResult`, and `evaluate_compatibility`.
- Produces: `CapabilityDiscoveryQuery`, `CapabilityCandidate`, `CapabilityDiscoveryResult`, and `discover_capabilities(query)`.

- [ ] **Step 1: Write failing discovery tests**

```python
query = CapabilityDiscoveryQuery(
    registry=ModelCapabilityRegistry(records=(record("model-a"),)),
    requirements=ModelCapabilityRequirements(evidence=("logical requirement",)),
)
result = discover_capabilities(query)
assert [candidate.record.model_id for candidate in result.candidates] == ["model-a"]
```

- [ ] **Step 2: Verify RED**

Run: `./.venv/Scripts/python.exe -m pytest tests/test_model_capability_discovery.py -q`

Expected: collection fails because `mercury.models.discovery` does not exist.

- [ ] **Step 3: Implement evaluator-backed candidate construction**

```python
def discover_capabilities(query: CapabilityDiscoveryQuery) -> CapabilityDiscoveryResult:
    candidates = []
    for record in query.registry.records:
        compatibility = evaluate_compatibility(record, query.requirements)
        if compatibility.status is CompatibilityStatus.COMPATIBLE:
            candidates.append(CapabilityCandidate(record=record, compatibility=compatibility))
    return CapabilityDiscoveryResult(requirements=query.requirements, candidates=tuple(candidates))
```

Validate that candidates are exactly compatible, preserve their source record/evidence, sort only by canonical identity, and reject malformed query state.

- [ ] **Step 4: Verify GREEN**

Run: `./.venv/Scripts/python.exe -m pytest tests/test_model_capability_discovery.py -q`

Expected: all focused discovery tests pass.

- [ ] **Step 5: Run regression verification**

Run: `./.venv/Scripts/python.exe -m pytest tests -q`

Expected: the complete project suite passes with no changes outside Task 4.
