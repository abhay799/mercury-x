# Model & Hardware Registries Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build deterministic pre-development model and hardware registries over the certified v1 profile contracts without adding scheduling or placement logic.

**Architecture:** The registry layer stores immutable `ModelProfile` and `HardwareProfile` records, rejects duplicate identities, supports exact lookup, and performs non-ranking hard-attribute filtering. JSON loaders validate starter catalogs through the existing Pydantic contracts. Starter catalog entries are explicitly SIMULATED so they cannot be mistaken for measured benchmark data.

**Tech Stack:** Python 3.13, Pydantic v2, pytest, JSON.

**Spec:** `docs/MERCURY_X_MASTER_SPEC.md`

## Global Constraints

- Preserve `mercury.model.profile/v1` and `mercury.hardware.profile/v1` contracts.
- Do not add model ranking, scheduler decisions, or hardware placement policy in this step.
- Do not represent simulated hardware or model characteristics as measured evidence.
- Duplicate registry IDs must fail explicitly.
- Registry query order must remain deterministic and must not imply quality ranking.

---

### Task 1: Registry identity and lookup

**Files:**
- Create: `src/mercury/registry/errors.py`
- Create: `src/mercury/registry/model_registry.py`
- Create: `src/mercury/registry/hardware_registry.py`
- Test: `tests/test_registries.py`

**Interfaces:**
- Consumes: `ModelProfile`, `HardwareProfile`
- Produces: `ModelRegistry.register/get/ids/all`, `HardwareRegistry.register/get/ids/all`

- [x] Write failing tests for package absence and registry behavior.
- [x] Verify RED due to missing `mercury.registry` package.
- [x] Implement duplicate-safe registration and exact lookup.
- [x] Run registry tests.

### Task 2: Deterministic non-ranking filters

**Files:**
- Modify: `src/mercury/registry/model_registry.py`
- Modify: `src/mercury/registry/hardware_registry.py`
- Test: `tests/test_registries.py`

**Interfaces:**
- Consumes: declared profile fields only.
- Produces: `ModelRegistry.find(...)`, `HardwareRegistry.find(...)`.

- [x] Test capability/precision and hard hardware attribute filtering.
- [x] Implement filtering without scores or winner selection.
- [x] Verify tests pass.

### Task 3: Validated simulated starter catalogs

**Files:**
- Create: `src/mercury/registry/catalog_loader.py`
- Create: `configs/registries/models.json`
- Create: `configs/registries/hardware.json`
- Test: `tests/test_registries.py`

**Interfaces:**
- Produces: `load_model_catalog(path)`, `load_hardware_catalog(path)`.

- [x] Test that catalogs validate and remain explicitly SIMULATED.
- [x] Add synthetic starter catalogs with no measured-performance claims.
- [x] Verify the registry and contract test suites.
