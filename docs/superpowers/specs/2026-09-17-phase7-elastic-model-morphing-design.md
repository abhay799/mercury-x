# MERCURY X — Phase 7 Elastic Model Morphing Design

**Date:** 2026-09-17
**Status:** Locked design
**Phase:** 7 — Elastic Model Morphing

## Objective
Phase 7 determines which certified structural variants of the same logical model lineage may be used for a workload stage under current workload, composition, precision, policy, and evidence constraints. It may produce zero, one, or many valid morph profiles.

It does not switch to an unrelated model family, choose hardware, place workloads, schedule execution, invoke runtime execution, perform live self-modification, or rank/select a winning morph profile.

## Boundary
Phase 7 answers: which explicitly certified structural variants of the same model lineage are permitted for this exact workload stage under current requirements?

It does not decide which morph is best, when to switch morphs at runtime, which device should execute the morph, which morph is cheapest/fastest, or whether an unregistered architecture transformation is safe.

## Certified Baseline Morph Dimensions
Exactly five:
1. DEPTH — certified shallower/deeper execution path, including registered early-exit or active-layer variants.
2. WIDTH — certified narrower/wider subnetwork or family-consistent width variant.
3. EXPERT — certified MoE expert subset/count configuration.
4. ADAPTER — certified adapter/LoRA configuration tied to the same base lineage.
5. HEAD_CONTEXT — certified attention-head and/or context-window structural configuration.

## Core Rule
A morph is valid only when explicitly declared for the exact model lineage and supported by required evidence. Never infer morph capability from model names, provider names, general architecture knowledge, raw user text, guessed layer/expert counts, or common deployment practice.

## Lineage Identity
Preserve:
- provider
- model family
- base model ID
- lineage ID
- source revision
- morph variant ID

No silent cross-family or incompatible revision substitution.

## Inputs
Phase 7 may consume:
- Phase 2 workload requirements
- Phase 3 logical graph requirements
- Phase 5 composition
- Phase 6 precision profile
- exact morph capability registry
- explicit morph policy
- explicit evidence constraints

## Components
1. Morph Contracts
2. Morph Capability Registry
3. Morph Requirement Derivation
4. Morph Compatibility Engine
5. Morph Profile Generator
6. Morph Validation Engine
7. Phase 7 Certification Layer

## Core Contracts
- MorphDimension
- MorphRequirement
- MorphEvidenceConstraint
- ModelMorphCapability
- MorphAssignment
- MorphProfileDraft
- MorphProfile
- MorphValidationIssue
- MorphProfileStatus
- MorphPhaseStatus
- MorphGenerationMetadata
- MorphPhaseResult

Public contracts are immutable and versioned.

## Statuses
Profile: VALID | REJECTED
Phase: READY | NOT_APPLICABLE | FAIL

READY: at least one valid morph profile exists where evaluation applies.
NOT_APPLICABLE: morphing is not required/permitted under certified state.
FAIL: morphing is required but no valid morph profile remains.

## No-Op Morph
A no-op profile is allowed only when the original structural state is itself a registered valid morph state. Do not invent one automatically.

## Dimension Rules
### DEPTH
Allowed only when exact lineage registers the depth variant, minimum active-depth requirements pass, evidence passes, and Phase 6 precision remains compatible.

### WIDTH
Allowed only when exact lineage registers the width/subnetwork variant and minimum capacity constraints pass.

### EXPERT
Allowed only when exact lineage is explicitly expert-morph capable, the exact expert subset/count is registered, evidence passes, and expert-capacity constraints pass.

### ADAPTER
Allowed only when the adapter is explicitly registered against the exact base lineage/revision, policy permits it, and adapter evidence passes.

### HEAD_CONTEXT
Allowed only when the exact head/context variant is registered, minimum context/head requirements pass, and Phase 6 precision compatibility remains valid.

## Precision Interaction
Phase 7 consumes Phase 6 but never overrides it. Reject any morph incompatible with the assigned precision profile. Phase 7 cannot select a new precision profile.

## Deterministic Generation
Canonical dimension order:
DEPTH → WIDTH → EXPERT → ADAPTER → HEAD_CONTEXT

Within each dimension, use stable registered variant identity only. Ordering is reproducibility-only, never preference.

Equivalent semantic inputs must yield equivalent profile IDs/order. IDs use stable SHA-256 canonical logical content only.

## Bounding
MAX_MORPH_PROFILES = 128.

Caller may request a smaller positive cap. Values <=0 or >128 fail closed.

Transparent truncation requires:
- truncated=true
- enumeration_completed=false
- lower_bound_unique_profiles >= cap + 1
- no exact unseen-total claim

## Semantic Deduplication
Signature includes:
- schema version
- composition ID
- precision profile ID
- ordered stage IDs
- exact lineage identities
- exact variant IDs
- morph dimensions
- hard requirement IDs

Never merge different revisions, lineages, variants, precision profiles, or hard requirements.

## Evidence
Evidence preserves claim, source, source revision, reference identity, state, provenance, and exact-lineage applicability.

Missing, stale, conflicting, invalid, or insufficient required evidence fails closed.

## Fail-Closed Rules
Reject/fail on:
- unknown morph dimension
- unknown/unregistered variant
- lineage/revision mismatch
- adapter/base mismatch
- invalid expert subset/count
- context below requirement
- depth below requirement
- precision incompatibility
- missing/stale/conflicting/invalid evidence
- malformed profile
- duplicate assignment
- missing/extra stage
- unsupported schema
- forbidden boundary leakage

No automatic repair, silent fallback, or cross-family substitution.

## Forbidden Behavior
No:
- rank
- score
- winner
- best/preferred morph
- fallback ordering
- selected model
- unrelated model-family substitution
- hardware/device matching
- placement
- scheduling
- runtime invocation
- live runtime morph switching
- autonomous self-modification
- cost/latency/quality optimization

## Immutability and Provenance
Do not mutate upstream workload, graph, composition, precision profiles, morph registry, policies, evidence, or source collections.

Every final profile remains traceable to workload, graph/composition, precision profile, exact model lineage, registered morph capability, requirements, policy, evidence, and generation reason.

## Multi-Candidate Isolation
Each profile is independent. One rejected profile does not poison valid profiles. True semantic duplicates may merge with deterministic provenance/evidence union; semantically distinct variants remain distinct.

## Testing Strategy
Cover contracts, exact five-dimension vocabulary, registry lookup/conflicts, no inference, requirements, each morph dimension, lineage/revision preservation, precision compatibility, evidence, invalid structural states, deterministic generation, dedup, 128 cap, transparent truncation, integration failures, boundary leakage, permutation determinism, immutability, and machine-readable certification.

## Implementation Tasks
1. Morph Contract Baseline
2. Morph Capability Registry
3. Morph Requirement Derivation
4. Morph Compatibility & Validation Engine
5. Morph Profile Generation & Bounding
6. Integration & Failure Hardening
7. Phase 7 Certification

## Exit Criteria
Phase 7 is complete only when:
- exactly five morph dimensions are certified
- exact lineage/revision is preserved
- only registered variants are emitted
- Phase 6 precision compatibility is respected
- no cross-family substitution occurs
- deterministic IDs/order are proven
- MAX_MORPH_PROFILES=128 is enforced
- invalid profiles fail closed
- valid/rejected isolation is proven
- no ranking/selection exists
- no hardware/placement/scheduling/runtime/self-modification leakage exists
- adversarial integration passes
- certification passes
- full regression passes

## Future Extensions
Outside the Phase 7 baseline:
- runtime morph switching
- telemetry-driven adaptation
- learned morph policies
- dynamic pruning
- speculative morph execution
- hardware-aware morph availability
- fine-grained per-layer morphing
- online expert restructuring
