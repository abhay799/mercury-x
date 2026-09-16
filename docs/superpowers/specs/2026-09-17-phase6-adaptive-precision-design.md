# MERCURY X — Phase 6 Adaptive Precision Design

**Date:** 2026-09-17
**Status:** Approved design draft for user review

## Objective
Phase 6 determines which numerical precision modes are safely allowed for each exact model stage in a certified Phase 5 composition. It may produce zero, one, or many valid precision profiles.

It does not choose the final model, hardware, placement, scheduler, runtime, execution order, or a preferred profile.

## Boundary
Phase 6 answers: which numerical precision assignments are permitted for this exact composition under certified workload, capability, evidence, and policy constraints?

It does not answer which profile is best, which hardware should execute it, how it should be scheduled, whether it is cheaper/faster, or when runtime precision should switch.

## Certified Baseline
Exactly four certified modes:
- FP32
- BF16
- FP16
- INT8

Canonical serialization/enumeration order: FP32 → BF16 → FP16 → INT8. This order is reproducibility-only and carries no preference.

Future modes such as FP8, INT4, per-layer precision, mixed quantization, and runtime precision switching remain outside the certified baseline.

## Components
1. Precision Contracts
2. Precision Requirement Derivation
3. Precision Capability Registry
4. Precision Compatibility Engine
5. Precision Profile Generator
6. Precision Validation Engine
7. Phase 6 Certification Layer

## Core Contracts
- PrecisionMode
- PrecisionRequirement
- ModelPrecisionCapability
- PrecisionAssignment
- PrecisionProfile
- PrecisionValidationIssue
- PrecisionCandidateStatus: VALID | REJECTED
- PrecisionPhaseStatus: READY | NOT_APPLICABLE | FAIL

All contracts are immutable and versioned. Unknown schema or mode values fail closed.

## Precision Rules
FP32: exact model revision must explicitly declare support.

BF16: exact revision must support BF16, reduced precision must be allowed, and any explicitly required evidence must be acceptable.

FP16: exact revision must support FP16, reduced precision must be allowed, and explicit numerical-stability or quality-preservation rules must not block it.

INT8: exact revision must explicitly support INT8/quantization, policy must allow it, and explicit quantization evidence is always required in the certified baseline.

No precision capability may be inferred from model names, aliases, providers, families, raw user text, or general deployment assumptions.

## Mixed Precision
Bounded mixed precision is certified.

A profile such as PRIMARY=FP16 and VERIFIER=FP32 may be valid only when every stage independently supports its assigned mode and all cross-stage hard requirements remain satisfied.

Phase 6 does not rank mixed profiles or choose which one executes.

## Requirement Sources
Hard precision requirements may come only from:
- exact Phase 5 composition/model identities
- certified Phase 2 workload requirements
- certified Phase 3 logical requirements where precision sensitivity is explicit
- explicit precision policy
- explicit evidence constraints

Raw text interpretation is not a certified requirement source.

## Deterministic Generation
For each certified Phase 5 composition:
1. preserve certified stage order
2. derive stage requirements
3. retrieve exact model-revision precision capabilities
4. compute each stage's allowed modes
5. enumerate uniform and mixed profiles deterministically
6. validate independently
7. semantically deduplicate
8. enforce certified bounds
9. preserve transparent generation metadata

Equivalent semantic inputs must produce equivalent IDs and canonical ordering.

Profile IDs use a stable digest of canonical logical content, never timestamps, random UUIDs, Python hash(), filesystem order, or machine-specific state.

## Bound
MAX_PRECISION_PROFILES = 128.

A caller may request a smaller positive limit but may not exceed the certified maximum. Truncation must be explicit and must not claim an exact unseen total.

## Evidence Policy
Evidence preserves claim, source, source revision, reference identity, state, provenance, and applicability to the exact model revision.

- FP32: normal capability provenance is sufficient unless stricter evidence is explicitly required.
- BF16/FP16: extra evidence only when explicitly required.
- INT8: explicit quantization evidence is always required.
- stale, conflicting, invalid, or insufficient required evidence fails closed.

## Validation
A profile is VALID only if every hard invariant passes. Otherwise it is REJECTED with stable deterministic issues.

Validation checks exact stage coverage, no extra stages, exact model identity/revision, declared precision support, evidence, mixed-profile integrity, deterministic ID, provenance, justification, and absence of forbidden boundary leakage.

Validation never repairs a profile.

## Result Semantics
READY: at least one valid profile exists where Phase 6 evaluation applies.

NOT_APPLICABLE: precision adaptation is not required under certified rules.

FAIL: precision adaptation is required and no valid profile remains.

One rejected profile never poisons another valid profile.

## Fail-Closed Rules
Unknown, malformed, unsupported, incomplete, or inconsistent hard state must never be guessed.

Examples:
- missing exact model revision
- unknown precision mode
- missing capability record
- unsupported precision mode
- missing/stale/conflicting required evidence
- INT8 without certified quantization support/evidence
- malformed profile
- duplicate stage assignment
- missing or extra stage
- model/stage identity mismatch
- unsupported schema
- forbidden boundary leakage

No silent precision downgrade is allowed.

## Forbidden Phase 6 Behavior
Phase 6 must not expose or perform:
- rank
- score
- winner
- best profile
- preferred precision
- fallback ordering
- selected model
- hardware/device matching
- placement
- scheduler assignment
- runtime invocation
- runtime precision switching
- cost optimization
- latency optimization
- quality optimization

## Provenance and Immutability
Phase 6 does not mutate upstream workload, graph, model capability, Phase 5 composition, registry, policy, evidence, or source profile inputs.

Every final profile remains traceable to workload, graph/composition, exact model revisions, capability records, requirements, evidence, policy, and generation reason.

## Testing Strategy
Cover:
- immutable/versioned contracts
- exact four-mode vocabulary
- exact identity/revision handling
- registry conflict handling
- no name-based inference
- requirement derivation provenance
- FP32/BF16/FP16/INT8 compatibility rules
- mandatory INT8 evidence
- mixed precision
- zero/one/many profile generation
- deterministic IDs and permutations
- semantic deduplication
- 128-profile cap and transparent truncation
- adversarial integration failures
- boundary leakage
- source immutability
- machine-readable certification

## Implementation Tasks
Task 1 — Precision Contract Baseline

Task 2 — Precision Capability Registry

Task 3 — Precision Requirement Derivation

Task 4 — Precision Compatibility & Validation Engine

Task 5 — Precision Profile Generation & Bounding

Task 6 — Integration & Failure Hardening

Task 7 — Phase 6 Certification

## Exit Criteria
Phase 6 is complete only when:
- exactly FP32/BF16/FP16/INT8 are certified
- exact model revision identity is preserved
- precision capabilities are evidence-backed
- INT8 always requires explicit quantization evidence
- uniform and bounded mixed profiles work
- deterministic profile IDs/order are proven
- MAX_PRECISION_PROFILES=128 is enforced
- invalid profiles fail closed
- valid/rejected profile isolation is proven
- no ranking/selection exists
- no hardware/placement/scheduling/runtime/optimization leakage exists
- adversarial integration tests pass
- certification passes
- full repository regression passes
