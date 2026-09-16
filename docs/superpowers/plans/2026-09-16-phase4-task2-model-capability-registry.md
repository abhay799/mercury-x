# Phase 4 Task 2: Model Capability Registry Baseline

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Provide an immutable, deterministic catalog of Phase 4 model capability records for exact identity lookup and descriptive filtering.

**Architecture:** `ModelCapabilityRegistry` composes Task 1 `ModelCapabilityRecord` values without copying or changing them. It canonicalizes equivalent duplicate entries by the full provider/model/family/revision identity, rejects conflicts, and derives an SHA-256 snapshot fingerprint solely from canonical serialized content.

**Tech Stack:** Python 3, Pydantic v2, hashlib, pytest.

**Spec:** Locked Phase 4 Task 2 request, 2026-09-16.

## Global Constraints

- Create only this plan, `src/mercury/models/registry.py`, and `tests/test_model_capability_registry.py`.
- Reuse the Phase 4 Task 1 capability contract unchanged.
- Permit only exact lookup, stable listing, and descriptive metadata filtering.
- Do not rank, select, route, compose, place, schedule, or invoke models.
- Do not fetch metadata or use network access.

---

### Task 1: Deterministic Capability Registry

**Files:**
- Create: `src/mercury/models/registry.py`
- Test: `tests/test_model_capability_registry.py`

**Interfaces:**
- Consumes: `ModelCapabilityRecord`, `ModelModality`, and `CapabilityStatus` from `mercury.models.capabilities`.
- Produces: `ModelCapabilityRegistry(records=...)`, `lookup(provider, model_id, family, revision)`, `list_records()`, `filter(...)`, and `fingerprint`.

- [ ] **Step 1: Write failing registry tests**

```python
registry = ModelCapabilityRegistry(records=(record("model-b"), record("model-a")))
assert registry.lookup("provider-a", "model-a", "family-a", "v1").model_id == "model-a"
assert registry.filter(declared_capability="tool_use") == ()
```

- [ ] **Step 2: Verify RED**

Run: `./.venv/Scripts/python.exe -m pytest tests/test_model_capability_registry.py -q`

Expected: collection fails because `mercury.models.registry` does not exist.

- [ ] **Step 3: Implement frozen registration and exact APIs**

```python
class ModelCapabilityRegistry(ContractModel):
    records: tuple[ModelCapabilityRecord, ...] = ()

    def lookup(self, provider: str, model_id: str, family: str, revision: str) -> ModelCapabilityRecord: ...
    def list_records(self) -> tuple[ModelCapabilityRecord, ...]: ...
    def filter(self, *, provider: str | None = None, ...) -> tuple[ModelCapabilityRecord, ...]: ...
```

Normalize records with a stable full identity key, fail on conflicting values for that key, return no implicit revision, and construct the fingerprint from JSON with sorted keys and stable separators. Filtering may only inspect declared record attributes and must return canonical order.

- [ ] **Step 4: Verify GREEN**

Run: `./.venv/Scripts/python.exe -m pytest tests/test_model_capability_registry.py -q`

Expected: all focused registry tests pass.

- [ ] **Step 5: Run regression verification**

Run: `./.venv/Scripts/python.exe -m pytest tests -q`

Expected: the complete project suite passes without changes outside Task 2.
