# Phase 4 Task 1: Model Capability Contract Baseline

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Define deterministic, immutable, provenance-aware metadata describing declared capabilities of a single model without making selection or execution decisions.

**Architecture:** `ModelCapabilityRecord` is a strict frozen contract that composes a frozen provenance record with enum-based modality, reasoning, provenance-kind, and lifecycle declarations. Tuple normalization gives stable equality and serialization while preserving unknown limits as `None` rather than inventing a numeric default.

**Tech Stack:** Python 3, Pydantic v2, pytest.

**Spec:** Locked Phase 4 Task 1 request, 2026-09-16.

## Global Constraints

- Create only this plan, `src/mercury/models/capabilities.py`, and `tests/test_model_capabilities.py`.
- Reuse `ContractModel` for strict frozen validation.
- Describe capabilities only; do not rank, select, route, place, schedule, or execute models.
- Do not fetch external metadata or use network access.
- Normalize only deterministic collections and do not manufacture limits or capability claims.

---

### Task 1: Model Capability Contract

**Files:**
- Create: `src/mercury/models/capabilities.py`
- Test: `tests/test_model_capabilities.py`

**Interfaces:**
- Consumes: `mercury.contracts.base.ContractModel`.
- Produces: `ModelModality`, `ReasoningCapability`, `CapabilityStatus`, `ProvenanceKind`, `CapabilityProvenance`, and `ModelCapabilityRecord`.

- [ ] **Step 1: Write failing contract tests**

```python
record = ModelCapabilityRecord(
    model_id="example-text-v1", provider="example-provider",
    family="example-family", revision="2026-09",
    input_modalities=(ModelModality.TEXT,),
    output_modalities=(ModelModality.TEXT,),
    provenance=CapabilityProvenance(
        source="declared registry", source_revision="2026-09",
        evidence="provider capability declaration",
    ),
)
assert record.to_dict()["model_id"] == "example-text-v1"
```

- [ ] **Step 2: Verify RED**

Run: `./.venv/Scripts/python.exe -m pytest tests/test_model_capabilities.py -q`

Expected: collection fails because `mercury.models.capabilities` does not exist.

- [ ] **Step 3: Add the minimal frozen descriptive contract**

```python
class ModelCapabilityRecord(ContractModel):
    schema_version: Literal["mercury.model-capability/v1"] = "mercury.model-capability/v1"
    model_id: str
    provider: str
    family: str
    revision: str
    input_modalities: tuple[ModelModality, ...]
    output_modalities: tuple[ModelModality, ...]
    provenance: CapabilityProvenance
```

Use validators to reject blank identity/provenance, normalize enum tuples by enum value, reject invalid declared limits, and exclude unknown extra fields. Include only descriptive booleans for tools, retrieval, code, structured output, streaming, batching, and deterministic-seed support.

- [ ] **Step 4: Verify GREEN**

Run: `./.venv/Scripts/python.exe -m pytest tests/test_model_capabilities.py -q`

Expected: all focused contract tests pass.

- [ ] **Step 5: Run regression verification**

Run: `./.venv/Scripts/python.exe -m pytest tests -q`

Expected: all project tests pass with no production-file changes outside this task.
