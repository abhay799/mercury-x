# Phase 7 Elastic Model Morphing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build MERCURY X Phase 7 Elastic Model Morphing so it deterministically derives, validates, and bounds registered structural morph profiles for exact model lineages while respecting Phase 6 precision constraints and avoiding ranking, hardware, scheduling, runtime, or self-modification leakage.

**Architecture:** Phase 7 consumes certified workload/composition/precision artifacts plus an exact lineage morph registry, explicit morph policy, and evidence. It derives hard morph requirements, checks lineage-specific compatibility, generates only registered variants, independently validates profiles, deduplicates/bounds them, and returns `READY`, `NOT_APPLICABLE`, or `FAIL`.

**Tech Stack:** Python 3, Pydantic immutable contracts, existing MERCURY certification framework, pytest, SHA-256 canonical digests.

**Spec:** `docs/superpowers/specs/2026-09-17-phase7-elastic-model-morphing-design.md`

## Global Constraints

- Certified morph dimensions are exactly: `DEPTH`, `WIDTH`, `EXPERT`, `ADAPTER`, `HEAD_CONTEXT`.
- `MAX_MORPH_PROFILES = 128`.
- Exact lineage identity preserves provider, family, base model ID, lineage ID, source revision, and morph variant ID.
- Only explicitly registered variants may be emitted.
- Phase 7 must respect the exact Phase 6 precision profile and must not change precision.
- No cross-family substitution.
- No inference from raw prompt/user text, model names, provider names, guessed architecture values, aliases, or common deployment assumptions.
- No ranking, scoring, winner, best/preferred morph, fallback ordering, selected model, hardware/device matching, placement, scheduler decisions, runtime execution, live morph switching, autonomous self-modification, cost optimization, latency optimization, or quality optimization.
- Unknown, malformed, unsupported, incomplete, or inconsistent hard state fails closed.
- Validation never repairs a profile.
- Source inputs and result collections are immutable.
- Use TDD: focused RED → minimal GREEN → focused GREEN → full suite exactly once per task.
- Do not create a worktree for this user workflow.
- Do not modify certified prior phases unless a Phase 7 integration test proves a real incompatibility; if so, stop and report before broad changes.

---

## File Structure

- `src/mercury/morphing/contracts.py` — public Phase 7 enums/contracts, lineage identity, profile/result types, deterministic IDs.
- `src/mercury/morphing/registry.py` — exact lineage/revision morph capability registry.
- `src/mercury/morphing/requirements.py` — explicit stage-level morph requirement derivation.
- `src/mercury/morphing/compatibility.py` — exact morph compatibility and evidence evaluation.
- `src/mercury/morphing/validation.py` — independent profile validation.
- `src/mercury/morphing/generation.py` — registered-only generation, deduplication, 128-profile bounding, final result aggregation.
- `src/mercury/certification/phase7.py` — Phase 7 certification evaluator.
- `configs/certification/phase7.json`
- `tests/test_morphing_contracts.py`
- `tests/test_morphing_registry.py`
- `tests/test_morphing_requirements.py`
- `tests/test_morphing_compatibility_validation.py`
- `tests/test_morphing_generation.py`
- `tests/test_morphing_integration_failures.py`
- `tests/test_phase7_certification.py`

---

### Task 1: Morph Contract Baseline

**Files:**
- Create: `src/mercury/morphing/contracts.py`
- Test: `tests/test_morphing_contracts.py`

**Interfaces:**
- Produces:
  - `MorphDimension`
  - `MorphRequirement`
  - `MorphEvidenceConstraint`
  - `ModelMorphCapability`
  - `MorphAssignment`
  - `MorphProfileDraft`
  - `MorphProfile`
  - `MorphValidationIssue`
  - `MorphProfileStatus`
  - `MorphPhaseStatus`
  - `MorphGenerationMetadata`
  - `MorphPhaseResult`
  - `canonical_morph_profile_payload(...)`
  - `morph_profile_id(...)`

**Required behavior:**
- exact dimension vocabulary: `DEPTH`, `WIDTH`, `EXPERT`, `ADAPTER`, `HEAD_CONTEXT`;
- profile status exactly `VALID`, `REJECTED`;
- phase status exactly `READY`, `NOT_APPLICABLE`, `FAIL`;
- immutable public contracts;
- required identity/provenance/reason fields reject blanks;
- deterministic SHA-256 IDs with `sha256:` prefix;
- identity includes schema, composition ID, precision profile ID, ordered stages, exact lineage, exact variant IDs, dimensions, and hard requirement IDs;
- forbidden public fields include rank/score/winner/best/preferred/fallback/hardware/device/placement/scheduler/runtime.

- [ ] **Step 1: Write failing contract tests**
- [ ] **Step 2: Run**
```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_morphing_contracts.py -q
```
Expected: RED.
- [ ] **Step 3: Implement minimal contracts and deterministic IDs**
- [ ] **Step 4: Run focused tests until GREEN**
- [ ] **Step 5: Run full suite exactly once**
```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```
- [ ] **Step 6: Commit**
```text
feat: add Phase 7 morphing contracts
```

---

### Task 2: Morph Capability Registry

**Files:**
- Create: `src/mercury/morphing/registry.py`
- Test: `tests/test_morphing_registry.py`

**Interfaces:**
- Produces:
  - `ModelMorphCapabilityRegistry`
  - `MorphRegistryIssue`
  - `canonical_morph_lineage_identity(record)`
  - `lookup_exact_morph_capability(...)`
  - deterministic registry fingerprint

**Required behavior:**
- exact lineage/revision lookup only;
- deterministic insertion-order-independent registry;
- exact semantic duplicates may collapse;
- conflicts for same exact identity fail closed;
- different revisions/lineages remain distinct;
- preserve evidence/provenance;
- no alias/fuzzy/name/provider/family inference.

- [ ] Write RED tests for exact lookup, permutation fingerprint, conflict handling, revision isolation, no name inference, evidence preservation.
- [ ] Run:
```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_morphing_registry.py -q
```
- [ ] Implement minimal registry.
- [ ] Focused GREEN.
- [ ] Full suite once.
- [ ] Commit:
```text
feat: add Phase 7 morph capability registry
```

---

### Task 3: Morph Requirement Derivation

**Files:**
- Create: `src/mercury/morphing/requirements.py`
- Test: `tests/test_morphing_requirements.py`

**Interfaces:**
- Produces:
  - `StageMorphRequirementSet`
  - `MorphRequirementDerivationResult`
  - `derive_morph_requirements(request)`

**Hard rules may express:**
- morphing forbidden;
- allowed/denied morph dimensions;
- minimum active depth;
- maximum allowed depth reduction;
- allowed width/subnetwork variants;
- expert count/subset constraints;
- required/forbidden adapters;
- minimum context/head requirements;
- explicit evidence requirements.

**Must preserve:**
- exact Phase 5 stage/model identity;
- exact Phase 6 precision profile ID;
- source artifact IDs and provenance.

**Forbidden:**
- raw-text guessing;
- model-name/provider inference;
- hardware/cost/latency/scheduler/runtime logic.

- [ ] RED tests for single/multi-stage derivation, deterministic output, each explicit requirement type, no raw-text inference, identity mismatch fail-closed, provenance, immutability.
- [ ] Run:
```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_morphing_requirements.py -q
```
- [ ] Implement minimal requirement derivation.
- [ ] Focused GREEN.
- [ ] Full suite once.
- [ ] Commit:
```text
feat: add Phase 7 morph requirement derivation
```

---

### Task 4: Morph Compatibility & Validation Engine

**Files:**
- Create: `src/mercury/morphing/compatibility.py`
- Create: `src/mercury/morphing/validation.py`
- Test: `tests/test_morphing_compatibility_validation.py`

**Interfaces:**
- Produces:
  - `MorphCompatibilityResult`
  - `evaluate_morph_compatibility(...)`
  - `validate_morph_profile(...)`

**Dimension rules:**
- DEPTH: exact registered variant; depth hard rules satisfied; evidence and Phase 6 precision compatibility pass.
- WIDTH: exact registered width/subnetwork; minimum capacity rules pass.
- EXPERT: exact registered subset/count; expert capacity and routing/evidence rules pass.
- ADAPTER: exact adapter tied to exact base lineage/revision; policy/evidence pass.
- HEAD_CONTEXT: exact registered head/context variant; minimum context/head rules pass.

**Validation rules:**
- exactly one stage morph assignment where required;
- no missing/extra/duplicate stage;
- exact lineage/revision/variant preserved;
- registered variant only;
- Phase 6 precision compatibility maintained;
- deterministic profile ID correct;
- provenance/justification nonblank;
- no repair/silent fallback/cross-family substitution;
- reject nested leakage such as best_morph, preferred_morph, best_model, rank, score, hardware, placement, scheduler, runtime.

- [ ] RED tests for valid/invalid cases across all five dimensions, precision mismatch, lineage mismatch, unregistered variant, missing evidence, nested leakage, deterministic issues, immutability.
- [ ] Run:
```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_morphing_compatibility_validation.py -q
```
- [ ] Implement compatibility engine.
- [ ] Implement independent validation.
- [ ] Focused GREEN.
- [ ] Full suite once.
- [ ] Commit:
```text
feat: add Phase 7 morph compatibility validation
```

---

### Task 5: Morph Profile Generation & Bounding

**Files:**
- Create: `src/mercury/morphing/generation.py`
- Test: `tests/test_morphing_generation.py`

**Interfaces:**
- Produces:
  - `iter_morph_profile_drafts(...)`
  - `generate_morph_profiles(...)`

**Algorithm:**
1. preserve Phase 5 stage order;
2. preserve Phase 6 precision profile;
3. exact morph registry lookup;
4. compute applicable registered variants;
5. canonical dimension order: DEPTH → WIDTH → EXPERT → ADAPTER → HEAD_CONTEXT;
6. enumerate only registered combinations;
7. validate independently;
8. semantic deduplicate;
9. retain VALID and REJECTED separately;
10. enforce `MAX_MORPH_PROFILES = 128`.

**Bounding:**
- default 128;
- caller smaller positive limit allowed;
- reject <=0 or >128;
- prove truncation by observing first unique profile beyond cap;
- truncated result records lower bound and never claims exact unseen total.

**Result semantics:**
- READY: applicable and at least one valid profile;
- FAIL: morphing required and no valid profile;
- NOT_APPLICABLE: morphing not required/permitted.

- [ ] RED tests for zero/one/many profiles, mixed stage morphs, all five dimensions, deterministic permutations, semantic dedup, distinct revision/variant preservation, cap rules, truncation metadata, valid/rejected isolation, no ranking/runtime leakage.
- [ ] Run:
```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_morphing_generation.py -q
```
- [ ] Implement lazy registered-only generator and dedup.
- [ ] Focused GREEN.
- [ ] Full suite once.
- [ ] Commit:
```text
feat: add Phase 7 bounded morph generation
```

---

### Task 6: Integration & Failure Hardening

**Files:**
- Create: `tests/test_morphing_integration_failures.py`

**Production modification:** none expected.

**End-to-end path:**
Phase 5 composition → Phase 6 precision profile → morph requirements → exact morph registry → compatibility → generation → validation → dedup/bounding → final Phase 7 status.

**Cover:**
- each of the five certified morph dimensions;
- multi-stage mixed morph profile;
- mixed VALID + REJECTED;
- no valid profile + morph required = FAIL;
- NOT_APPLICABLE path.

**Adversarial cases:**
- lineage mismatch;
- revision mismatch;
- unknown/unregistered variant;
- cross-family substitution attempt;
- adapter/base mismatch;
- invalid expert subset/count;
- depth below minimum;
- context below minimum;
- Phase 6 precision mismatch;
- missing/stale/conflicting/invalid evidence;
- duplicate/missing/extra stage;
- nested best_morph/preferred_morph/best_model leakage;
- hardware/placement/scheduler/runtime/self-modification leakage;
- cap violation;
- deterministic permutations;
- source immutability.

- [ ] Write integration/adversarial tests.
- [ ] Run:
```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_morphing_integration_failures.py -q
```
- [ ] If a real Phase 7 defect is proven, make only the smallest exact fix and report invariant.
- [ ] Focused GREEN.
- [ ] Full suite once.
- [ ] Commit:
```text
test: harden Phase 7 morph integration boundaries
```

---

### Task 7: Phase 7 Certification

**Files:**
- Create: `configs/certification/phase7.json`
- Create: `src/mercury/certification/phase7.py`
- Test: `tests/test_phase7_certification.py`

**Certification gates must prove at minimum:**
1. contracts immutable and versioned;
2. exactly five certified dimensions;
3. canonical dimension order deterministic/non-preferential;
4. `MAX_MORPH_PROFILES = 128`;
5. exact lineage/revision preservation;
6. registered-only morph emission;
7. no name/provider/family inference;
8. Phase 6 precision compatibility enforced;
9. no cross-family substitution;
10. all five morph dimensions supported;
11. deterministic profile IDs/order;
12. semantic dedup preserves distinct lineages/revisions/variants;
13. READY/NOT_APPLICABLE/FAIL semantics correct;
14. adversarial fail-closed coverage exists;
15. no rank/score/winner/preference;
16. no hardware/placement;
17. no scheduler/runtime/self-modification;
18. no cost/latency/quality optimization leakage.

**Evaluator:**
- load config;
- reject missing/malformed/unsupported schema;
- reject duplicate gate IDs;
- reject unknown gates;
- fail on missing required artifacts;
- evaluate every gate;
- never silently skip;
- deterministic aggregate;
- PASS only when all required gates PASS;
- never hardcode PASS.

- [ ] RED certification tests for valid config, missing/malformed/unsupported config, duplicate/unknown gate, missing artifact, dimension count change, cap change, precision-compatibility invariant break, cross-family leakage, runtime/self-modification leakage.
- [ ] Run:
```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_phase7_certification.py -q
```
- [ ] Implement config/evaluator using prior certification conventions.
- [ ] Focused GREEN.
- [ ] Run:
```powershell
.\.venv\Scripts\python.exe -m mercury.certification.phase7
```
- [ ] Full suite once.
- [ ] Commit:
```text
certify: complete Phase 7 elastic model morphing
```

---

## Self-Review

### Spec Coverage
Covered: exact five morph dimensions, lineage identity, registered-only variants, Phase 6 precision interaction, deterministic IDs/order, semantic dedup, 128 cap, transparent truncation, fail-closed rules, no cross-family substitution, no ranking/hardware/scheduling/runtime/self-modification leakage, integration hardening, and machine-readable certification.

### Placeholder Scan
No TBD/TODO/future placeholders are used for required Phase 7 behavior.

### Type Consistency
Task 1 defines contracts used by Tasks 2–7; Task 2 provides exact registry lookup; Task 3 provides requirement sets; Task 4 provides compatibility/validation; Task 5 generates final bounded results; Task 6 proves integration/failures; Task 7 certifies locked invariants.

## Execution Order

`Task 1 → Task 2 → Task 3 → Task 4 → Task 5 → Task 6 → Task 7`

Do not begin the next task until the current task has focused GREEN, one full regression GREEN, a checkpoint, and a clean tree. Do not begin Phase 8 until Phase 7 certification is PASS.
