# Phase 6 Adaptive Precision Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build MERCURY X Phase 6 Adaptive Precision so it deterministically derives, validates, and bounds evidence-backed precision profiles for certified Phase 5 compositions without ranking, hardware placement, scheduling, runtime execution, or optimization leakage.

**Architecture:** Phase 6 consumes certified workload/composition artifacts, exact model-revision precision capabilities, explicit policy, and evidence. It derives hard precision requirements, evaluates exact stage/mode compatibility, generates deterministic uniform and mixed precision profiles, validates them independently, deduplicates/bounds them, and returns `READY`, `NOT_APPLICABLE`, or `FAIL`. The certified baseline supports exactly `FP32`, `BF16`, `FP16`, and `INT8`.

**Tech Stack:** Python 3, Pydantic contracts, dataclasses/enums where already conventional, existing MERCURY certification framework, pytest, SHA-256 canonical digests.

**Spec:** `docs/superpowers/specs/2026-09-17-phase6-adaptive-precision-design.md`

## Global Constraints

- Certified precision modes are exactly: `FP32`, `BF16`, `FP16`, `INT8`.
- Canonical mode order is `FP32`, `BF16`, `FP16`, `INT8`; ordering is reproducibility-only.
- `MAX_PRECISION_PROFILES = 128`.
- Exact model identity is `(provider, model_id, family, revision)` and must be preserved end-to-end.
- `INT8` always requires explicit acceptable quantization evidence in the certified baseline.
- No precision capability inference from raw user text, model names, aliases, providers, families, or common deployment assumptions.
- Phase 6 may produce zero, one, or many profiles and must not rank, score, select, prefer, or name a winner.
- No hardware/device matching, placement, scheduling, runtime invocation, runtime precision switching, cost optimization, latency optimization, or quality optimization.
- Unknown, malformed, unsupported, incomplete, or inconsistent hard state fails closed.
- Validation never repairs a profile.
- Source inputs and result collections are immutable.
- Use TDD: focused RED → minimal GREEN → focused GREEN → full suite exactly once per task.
- Do not create a worktree for this user workflow.
- Do not modify certified prior phases unless a failing Phase 6 integration test proves a real incompatibility; if so, stop and report before broad changes.

---

## File Structure

Planned Phase 6 files:

- `src/mercury/precision/contracts.py` — public Phase 6 schemas, enums, immutable result/profile types, deterministic canonical identity helpers.
- `src/mercury/precision/registry.py` — exact model-revision precision capability registry and deterministic lookup/conflict handling.
- `src/mercury/precision/requirements.py` — derivation of stage-level precision hard requirements from certified upstream artifacts and explicit policy.
- `src/mercury/precision/compatibility.py` — exact stage/mode compatibility and evidence evaluation.
- `src/mercury/precision/validation.py` — independent profile validation and deterministic issues.
- `src/mercury/precision/generation.py` — uniform/mixed profile enumeration, semantic deduplication, 128-profile bounding, truncation metadata, final result aggregation.
- `src/mercury/certification/phase6.py` — machine-readable Phase 6 certification evaluator.
- `configs/certification/phase6.json` — stable Phase 6 certification gates.
- `tests/test_precision_contracts.py`
- `tests/test_precision_registry.py`
- `tests/test_precision_requirements.py`
- `tests/test_precision_compatibility_validation.py`
- `tests/test_precision_generation.py`
- `tests/test_precision_integration_failures.py`
- `tests/test_phase6_certification.py`

---

### Task 1: Precision Contract Baseline

**Files:**
- Create: `src/mercury/precision/contracts.py`
- Test: `tests/test_precision_contracts.py`

**Interfaces:**
- Consumes: existing Phase 4 exact model identity conventions and Phase 5 composition identities.
- Produces:
  - `PrecisionMode`
  - `PrecisionRequirement`
  - `PrecisionEvidenceConstraint`
  - `ModelPrecisionCapability`
  - `PrecisionAssignment`
  - `PrecisionProfileDraft`
  - `PrecisionProfile`
  - `PrecisionValidationIssue`
  - `PrecisionProfileStatus`
  - `PrecisionPhaseStatus`
  - `PrecisionGenerationMetadata`
  - `PrecisionPhaseResult`
  - `canonical_precision_profile_payload(...)`
  - `precision_profile_id(...)`

**Required contract behavior:**
- `PrecisionMode` has exactly `FP32`, `BF16`, `FP16`, `INT8`.
- `PrecisionProfileStatus` has exactly `VALID`, `REJECTED`.
- `PrecisionPhaseStatus` has exactly `READY`, `NOT_APPLICABLE`, `FAIL`.
- All public Phase 6 contracts are immutable.
- All identity/provenance/reason fields that are required must reject blanks.
- Duplicate stage assignments reject at contract or validation boundary as appropriate.
- Deterministic profile ID uses `sha256:` prefix and canonical semantic content.
- Forbidden public fields include: `rank`, `score`, `winner`, `best_profile`, `preferred_precision`, `fallback`, `selected_model`, `hardware`, `device`, `placement`, `scheduler`, `runtime`, `cost`, `latency`, `quality_optimization`.

- [ ] **Step 1: Write focused failing tests**

Cover at minimum:
```python
def test_precision_mode_vocabulary_is_exact():
    assert tuple(item.value for item in PrecisionMode) == ("FP32", "BF16", "FP16", "INT8")

def test_precision_status_vocabularies_are_exact():
    assert tuple(item.value for item in PrecisionProfileStatus) == ("VALID", "REJECTED")
    assert tuple(item.value for item in PrecisionPhaseStatus) == ("READY", "NOT_APPLICABLE", "FAIL")

def test_equivalent_profile_payload_produces_same_sha256_id():
    first = precision_profile_id(profile_a)
    second = precision_profile_id(equivalent_profile_a)
    assert first == second
    assert first.startswith("sha256:")

def test_contracts_expose_no_forbidden_phase6_decisions():
    forbidden = {
        "rank", "score", "winner", "best_profile", "preferred_precision",
        "selected_model", "hardware", "device", "placement",
        "scheduler", "runtime"
    }
    for contract in PUBLIC_CONTRACT_TYPES:
        assert forbidden.isdisjoint(contract.model_fields)
```

- [ ] **Step 2: Run focused tests and verify RED**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_precision_contracts.py -q
```

Expected: failures because Phase 6 contracts do not exist yet.

- [ ] **Step 3: Implement minimal immutable contracts**

Implement the exact interfaces above. Canonical profile identity must include:
- schema version;
- composition ID;
- ordered stage IDs;
- exact `(provider, model_id, family, revision)` identity for every assignment;
- assigned `PrecisionMode`;
- hard requirement identities.

Do not include provenance ordering noise, timestamps, machine state, filesystem state, cost/latency, or rank in the digest.

- [ ] **Step 4: Run focused tests until GREEN**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_precision_contracts.py -q
```

- [ ] **Step 5: Run full suite exactly once**

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

- [ ] **Step 6: Checkpoint**

Allowed files only:
```text
src/mercury/precision/contracts.py
tests/test_precision_contracts.py
```

Commit:
```text
feat: add Phase 6 precision contracts
```

---

### Task 2: Precision Capability Registry

**Files:**
- Create: `src/mercury/precision/registry.py`
- Test: `tests/test_precision_registry.py`

**Interfaces:**
- Consumes: `ModelPrecisionCapability`, `PrecisionMode`.
- Produces:
  - `ModelPrecisionCapabilityRegistry`
  - `PrecisionRegistryIssue`
  - `canonical_precision_model_identity(record)`
  - `lookup_exact_precision_capability(registry, provider, model_id, family, revision)`
  - deterministic registry `fingerprint`

**Required behavior:**
- Exact identity lookup only.
- Revision isolation is strict.
- Registry ordering is deterministic and independent of insertion order.
- Exact duplicate declarations may collapse only when semantically identical.
- Conflicting declarations for the same exact identity fail closed.
- Different revisions remain distinct.
- No aliases, fuzzy matching, model-name inference, provider preference, or family-default precision inference.
- Evidence/provenance remains attached to each supported precision claim.

- [ ] **Step 1: Write failing registry tests**

Include:
```python
def test_registry_lookup_requires_exact_revision():
    assert lookup_exact_precision_capability(registry, "p", "m", "f", "r1") == r1
    assert lookup_exact_precision_capability(registry, "p", "m", "f", "r2") == r2

def test_registry_permutation_has_same_fingerprint():
    assert registry_a.fingerprint == registry_b.fingerprint

def test_conflicting_same_identity_declarations_fail_closed():
    with pytest.raises(ValidationError):
        ModelPrecisionCapabilityRegistry(records=(first, conflicting))
```

Also test:
- empty registry;
- semantically identical duplicate handling;
- evidence/provenance preservation;
- model name containing `"int8"` cannot create INT8 support;
- provider name cannot imply preferred precision.

- [ ] **Step 2: Verify RED**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_precision_registry.py -q
```

- [ ] **Step 3: Implement minimal registry**

Use exact canonical identity sorting:
```text
provider
model_id
family
revision
```

Fingerprint must use canonical serialized registry content and SHA-256.

- [ ] **Step 4: Run focused GREEN**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_precision_registry.py -q
```

- [ ] **Step 5: Run full suite exactly once**

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

- [ ] **Step 6: Checkpoint**

Allowed:
```text
src/mercury/precision/registry.py
tests/test_precision_registry.py
```

Commit:
```text
feat: add Phase 6 precision capability registry
```

---

### Task 3: Precision Requirement Derivation

**Files:**
- Create: `src/mercury/precision/requirements.py`
- Test: `tests/test_precision_requirements.py`

**Interfaces:**
- Consumes:
  - certified Phase 2 workload intelligence result;
  - certified Phase 3 graph/readiness artifacts;
  - certified Phase 5 composition candidate;
  - explicit `PrecisionRequirement` / policy inputs.
- Produces:
  - `StagePrecisionRequirementSet`
  - `PrecisionRequirementDerivationResult`
  - `derive_precision_requirements(request)`

**Derivation rules:**
- Preserve exact Phase 5 stage/model identity.
- Derive only from explicit certified state.
- `reduced_precision_forbidden=True` blocks BF16, FP16, INT8.
- `quantization_forbidden=True` blocks INT8.
- Explicit mode allow/deny constraints are hard rules.
- Numerical stability, structured-output sensitivity, and reasoning sensitivity affect compatibility only when explicitly represented upstream/policy.
- Raw prompt/user text must never be parsed to decide precision safety.
- No hardware, accelerator, device, cost, latency, scheduler, runtime, or optimization inputs.
- All derived requirements preserve source artifact IDs and evidence/provenance.

- [ ] **Step 1: Write focused failing tests**

Test:
- one stage derives stable identity-linked requirement set;
- multi-stage composition derives one set per declared stage;
- repeated equivalent input gives identical result;
- explicit reduced precision ban propagates;
- explicit quantization ban propagates;
- no raw text keyword inference (`"must be accurate"`, `"int8"`, `"gpu"`) changes requirements;
- no provider/model-name inference;
- upstream identity mismatch fails closed;
- blocked/unready graph fails closed where required by existing contracts;
- provenance is nonblank and stable;
- inputs remain immutable.

- [ ] **Step 2: Verify RED**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_precision_requirements.py -q
```

- [ ] **Step 3: Implement minimal derivation**

Do not perform mode compatibility here. This task derives requirements only.

- [ ] **Step 4: Run focused GREEN**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_precision_requirements.py -q
```

- [ ] **Step 5: Run full suite exactly once**

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

- [ ] **Step 6: Checkpoint**

Allowed:
```text
src/mercury/precision/requirements.py
tests/test_precision_requirements.py
```

Commit:
```text
feat: add Phase 6 precision requirement derivation
```

---

### Task 4: Precision Compatibility & Validation Engine

**Files:**
- Create: `src/mercury/precision/compatibility.py`
- Create: `src/mercury/precision/validation.py`
- Test: `tests/test_precision_compatibility_validation.py`

**Interfaces:**
- Consumes:
  - exact stage requirement set;
  - exact `ModelPrecisionCapability`;
  - `PrecisionEvidenceConstraint`;
  - `PrecisionProfileDraft`.
- Produces:
  - `PrecisionCompatibilityResult`
  - `evaluate_precision_compatibility(...)`
  - `validate_precision_profile(...)`
  - immutable `PrecisionProfile` with `VALID` or `REJECTED`.

**Compatibility rules:**

`FP32`:
- exact revision explicitly supports FP32;
- any explicitly required evidence passes.

`BF16`:
- exact revision supports BF16;
- reduced precision not forbidden;
- explicit BF16 evidence requirements pass.

`FP16`:
- exact revision supports FP16;
- reduced precision not forbidden;
- explicit numerical-stability/quality-preservation rule does not forbid FP16;
- explicit evidence requirements pass.

`INT8`:
- exact revision explicitly supports INT8;
- reduced precision not forbidden;
- quantization not forbidden;
- explicit acceptable quantization evidence is always present;
- any stricter explicit policy also passes.

**Validation rules:**
- exactly one assignment per certified Phase 5 stage;
- no missing or extra stages;
- exact stage/model identity preserved;
- every assignment has compatible mode result;
- profile ID recomputes correctly;
- provenance and capability justification are nonblank;
- unknown mode/schema/state fails closed;
- no hidden decision leakage fields or nested keys such as `best_profile`, `preferred_precision`, `best_model`, `rank`, `score`, hardware/placement/scheduler/runtime markers;
- no automatic repair or downgrade.

- [ ] **Step 1: Write focused RED tests**

At minimum:
- valid FP32 passes;
- BF16/FP16 reduced-precision ban rejects;
- FP16 stability rule rejects when explicit;
- INT8 without quantization evidence rejects;
- INT8 with acceptable evidence passes;
- stale/conflicting/invalid INT8 evidence rejects;
- unsupported exact revision rejects;
- model-name `"int8-ready"` cannot bypass capability;
- identity mismatch rejects;
- missing/extra/duplicate stage rejects;
- profile digest mismatch rejects;
- valid mixed profile passes;
- one invalid stage rejects the profile;
- nested forbidden decision leakage rejects;
- rejection issue ordering deterministic;
- validation leaves draft unchanged.

- [ ] **Step 2: Verify RED**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_precision_compatibility_validation.py -q
```

- [ ] **Step 3: Implement minimum compatibility engine**

Compatibility output must include:
- exact stage identity;
- mode;
- compatible boolean/status;
- stable issue/reason set;
- evidence assessment refs;
- provenance.

- [ ] **Step 4: Implement independent profile validation**

Validation calls compatibility or consumes its evidence; it must not regenerate or repair assignments.

- [ ] **Step 5: Focused GREEN**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_precision_compatibility_validation.py -q
```

- [ ] **Step 6: Full suite exactly once**

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

- [ ] **Step 7: Checkpoint**

Allowed:
```text
src/mercury/precision/compatibility.py
src/mercury/precision/validation.py
tests/test_precision_compatibility_validation.py
```

Commit:
```text
feat: add Phase 6 precision compatibility validation
```

---

### Task 5: Precision Profile Generation & Bounding

**Files:**
- Create: `src/mercury/precision/generation.py`
- Test: `tests/test_precision_generation.py`

**Interfaces:**
- Consumes:
  - Phase 5 certified composition;
  - stage requirement sets;
  - precision capability registry;
  - explicit evidence constraints;
  - optional caller `max_profiles`.
- Produces:
  - `iter_precision_profile_drafts(...)`
  - `generate_precision_profiles(...)`
  - final `PrecisionPhaseResult`.

**Generation algorithm:**
1. preserve Phase 5 certified stage order;
2. lookup exact precision capability for each stage;
3. compute allowed mode set using compatibility rules;
4. enumerate Cartesian stage/mode combinations in canonical mode order;
5. build deterministic profile drafts;
6. validate each profile independently;
7. semantic-deduplicate equivalent profiles;
8. retain valid and rejected profiles separately;
9. enforce `MAX_PRECISION_PROFILES = 128`;
10. report transparent truncation metadata.

**Semantic signature includes:**
- schema version;
- composition ID;
- ordered stage IDs/roles;
- exact model identity/revision;
- assigned precision mode;
- hard requirement identities.

Do not deduplicate semantically different modes or exact model revisions.

**Bounding:**
- default max = 128;
- caller smaller positive limit allowed;
- 0, negative, or >128 rejected;
- to prove truncation, observe the first unique profile beyond the cap;
- when truncated:
  - `truncated=True`
  - `enumeration_completed=False`
  - `lower_bound_unique_profiles >= cap + 1`
  - do not claim exact unseen total.

**Final result semantics:**
- `READY`: applicable and at least one valid profile exists;
- `FAIL`: adaptation required and no valid profile remains;
- `NOT_APPLICABLE`: adaptation not required under certified rules.

- [ ] **Step 1: Write focused failing generation tests**

Cover:
- one-stage FP32-only → one profile;
- zero supported modes → no valid profiles;
- multiple modes → deterministic multiple profiles;
- two-stage mixed combinations enumerate deterministically;
- permutation of registry/evidence input preserves semantic output;
- semantic duplicates merge;
- different mode remains distinct;
- different revision remains distinct;
- default 128 limit;
- smaller positive limit;
- invalid >128/zero/negative;
- exactly-at-cap exhaustive is not truncated;
- first unique over cap marks truncation;
- lower-bound metadata correct;
- valid/rejected isolation;
- rejected duplicate reason/provenance merge deterministic;
- no ranking/preference/cost/latency/hardware/scheduler/runtime fields.

- [ ] **Step 2: Verify RED**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_precision_generation.py -q
```

- [ ] **Step 3: Implement generator and semantic dedup**

Use lazy iteration. Do not materialize unbounded Cartesian combinations before enforcing the cap.

- [ ] **Step 4: Focused GREEN**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_precision_generation.py -q
```

- [ ] **Step 5: Full suite exactly once**

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

- [ ] **Step 6: Checkpoint**

Allowed:
```text
src/mercury/precision/generation.py
tests/test_precision_generation.py
```

Commit:
```text
feat: add Phase 6 bounded precision generation
```

---

### Task 6: Integration & Failure Hardening

**Files:**
- Create: `tests/test_precision_integration_failures.py`
- Production modification: none expected.

**Interfaces:**
- Exercises the complete Phase 6 public path:
  - certified upstream artifacts
  - requirement derivation
  - exact registry lookup
  - compatibility
  - profile generation
  - validation
  - deduplication/bounding
  - final result status.

**End-to-end scenarios:**
- FP32-only single-stage composition;
- BF16-capable composition;
- FP16-capable composition;
- INT8 with valid quantization evidence;
- multi-stage mixed precision;
- one invalid profile coexisting with valid profiles;
- no valid profile when adaptation required → `FAIL`;
- non-applicable state → `NOT_APPLICABLE`.

**Adversarial failures:**
- upstream identity mismatch;
- missing exact revision;
- empty registry;
- conflicting registry declaration;
- unsupported mode;
- model name pretending to advertise precision;
- missing INT8 evidence;
- stale/conflicting/invalid evidence;
- quantization forbidden;
- reduced precision forbidden;
- missing stage assignment;
- duplicate stage assignment;
- extra undeclared stage;
- nested `best_profile` / `preferred_precision` / `best_model` leakage;
- hardware/device/placement leakage;
- scheduler/runtime leakage;
- profile cap violation;
- deterministic permutation checks;
- source mutation attempts.

- [ ] **Step 1: Write integration/failure tests**

Production changes are not expected. If a focused test proves a real Phase 6 invariant defect, make only the smallest production fix needed and report the exact invariant.

- [ ] **Step 2: Run focused RED/GREEN cycle**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_precision_integration_failures.py -q
```

- [ ] **Step 3: If needed, apply one minimal proven production fix**

Do not broaden scope. Do not redesign prior tasks.

- [ ] **Step 4: Run focused tests until GREEN**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_precision_integration_failures.py -q
```

- [ ] **Step 5: Run full suite exactly once**

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

- [ ] **Step 6: Checkpoint**

Allowed by default:
```text
tests/test_precision_integration_failures.py
```

If a production invariant fix is proven, include only the exact affected Phase 6 production file.

Commit:
```text
test: harden Phase 6 precision integration boundaries
```

---

### Task 7: Phase 6 Certification

**Files:**
- Create: `configs/certification/phase6.json`
- Create: `src/mercury/certification/phase6.py`
- Test: `tests/test_phase6_certification.py`

**Interfaces:**
- Follow the existing MERCURY certification framework conventions used by prior certified phases.
- Produces a deterministic Phase 6 certification report and process exit behavior consistent with existing certification modules.

**Certification gates must prove at minimum:**
1. Phase 6 schema/contracts exist and are immutable.
2. Exactly four certified modes exist: FP32/BF16/FP16/INT8.
3. Canonical order is deterministic and non-preferential.
4. `MAX_PRECISION_PROFILES = 128`.
5. Exact model identity/revision is preserved.
6. Registry does not infer capability from names/aliases/providers/families.
7. INT8 always requires explicit acceptable quantization evidence.
8. BF16/FP16 obey explicit reduced-precision/stability constraints.
9. Uniform and bounded mixed precision are supported.
10. Deterministic profile IDs/order are proven.
11. Semantic deduplication preserves semantically distinct revisions/modes.
12. READY/NOT_APPLICABLE/FAIL semantics are correct.
13. Fail-closed adversarial coverage exists.
14. No rank/score/winner/preference/hardware/placement/scheduler/runtime/optimization leakage exists.

**Certification evaluator behavior:**
- load config;
- reject missing/malformed/unsupported schema;
- reject duplicate gate IDs;
- reject unknown gates;
- fail if required artifacts are missing;
- evaluate every configured gate;
- never silently skip;
- overall PASS only when all required gates PASS;
- never hardcode PASS.

- [ ] **Step 1: Write focused certification tests**

Include:
- valid config passes;
- missing config fails;
- malformed config fails;
- unsupported schema fails;
- duplicate gate ID fails;
- unknown gate fails;
- missing required source artifact fails;
- precision mode count change fails;
- certified cap change fails;
- INT8 evidence invariant break fails;
- forbidden boundary leakage fails;
- deterministic aggregate ordering.

- [ ] **Step 2: Verify RED**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_phase6_certification.py -q
```

- [ ] **Step 3: Implement certification config and evaluator**

Use prior certification phases for repository conventions only. Do not redesign the framework.

- [ ] **Step 4: Focused GREEN**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_phase6_certification.py -q
```

- [ ] **Step 5: Run Phase 6 certification**

```powershell
.\.venv\Scripts\python.exe -m mercury.certification.phase6
```

Expected: overall PASS with all configured gates PASS.

- [ ] **Step 6: Run full suite exactly once**

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

- [ ] **Step 7: Final Phase 6 checkpoint**

Allowed:
```text
configs/certification/phase6.json
src/mercury/certification/phase6.py
tests/test_phase6_certification.py
```

Commit:
```text
certify: complete Phase 6 adaptive precision
```

---

## Plan Self-Review

### Spec Coverage
Covered:
- exact four-mode baseline;
- precise architectural boundary;
- exact revision identity;
- evidence-backed capability;
- mandatory INT8 evidence;
- deterministic requirement derivation;
- compatibility;
- independent validation;
- uniform and mixed profile generation;
- semantic deduplication;
- 128-profile cap;
- transparent truncation;
- result semantics;
- fail-closed behavior;
- immutability/provenance;
- adversarial integration;
- machine-readable certification;
- no ranking/hardware/scheduling/runtime/optimization leakage.

### Placeholder Scan
No `TBD`, `TODO`, “implement later”, or undefined cross-task interfaces remain.

### Type/Interface Consistency
- Task 1 defines the core public contracts used by Tasks 2–7.
- Task 2 defines exact precision capability registry lookup used by Tasks 4–6.
- Task 3 defines stage requirement sets used by Tasks 4–6.
- Task 4 defines compatibility and independent validation used by Task 5.
- Task 5 owns final generation/bounding/result aggregation.
- Task 6 tests the complete integrated surface.
- Task 7 certifies the exact locked invariants above.

## Execution Order

Execute exactly:

`Task 1 → Task 2 → Task 3 → Task 4 → Task 5 → Task 6 → Task 7`

Do not begin the next task until the current task:
1. has focused tests GREEN;
2. has one full regression run GREEN;
3. has been reviewed/checkpointed;
4. leaves a clean working tree.

Do not begin Phase 7 until Phase 6 certification is PASS and the final Phase 6 checkpoint is clean.
