# MERCURY X — Phase 10 Context Prediction Engine Design

Date: 2026-09-17  
Status: Approved architecture  
Phase: 10 — Context Prediction Engine

## 1. Purpose

Phase 10 predicts which already-authorized context is likely to be needed next.

It produces bounded, explainable predictions with:

- target context key
- exact authorized namespace
- source lineage
- prediction horizon
- confidence score
- confidence band
- reason codes
- deterministic predictor identity/version

Phase 10 does **not** retrieve, persist, prefetch, place, cache, schedule, or execute context.

The boundary is:

> Phase 9 defines what durable context exists.  
> Phase 10 predicts what authorized context may be needed next.

## 2. Position in MERCURY X

The Phase 10 flow is:

```text
Phase 8 Session Memory
        +
Phase 9 Global Context Memory
        +
Explicit Task / Execution Context
        ↓
Prediction Candidate Builder
        ↓
Context Feature Engine
        ↓
Horizon & Confidence Engine
        ↓
Prediction Policy Guard
        ↓
Prediction Assembly & Ordering
        ↓
Context Prediction Result
```

Later phases may consume Phase 10 output, but Phase 10 itself must not perform their responsibilities.

Relationship to later phases:

- Phase 11 — Semantic KV Cache: may use predictions to inform reusable cache preparation.
- Phase 12+ — execution systems: may consume predictions for context-placement decisions.
- Phase 10 itself remains prediction-only.

## 3. Fundamental Rule

> Phase 10 predicts what authorized context may be useful next; it does not retrieve, persist, prefetch, place, cache, schedule, or execute that context.

## 4. Architectural Approach

Phase 10 uses a **hybrid deterministic predictor**.

The initial certified implementation uses:

- deterministic candidate construction
- transparent deterministic feature extraction
- deterministic scoring
- deterministic confidence bands
- deterministic horizon selection
- explicit reason codes
- fail-closed authorization and governance checks

Future learned predictors may be introduced behind the same contracts, but Phase 10 certification must not require opaque ML behavior.

This avoids two extremes:

1. Rule-only logic that is too weak to be useful.
2. Opaque learned prediction that would make Phase 10 difficult to explain, reproduce, certify, and govern.

## 5. Certified Prediction Horizons

Phase 10 supports exactly three prediction horizons:

```text
NEXT_TURN
NEXT_TASK
SESSION_NEAR_TERM
```

Definitions:

### NEXT_TURN
Context likely required in the immediately following interaction or reasoning step.

### NEXT_TASK
Context likely required during the next distinct task or execution unit within the current workflow.

### SESSION_NEAR_TERM
Context likely required later in the current authorized session, but not necessarily in the next turn or task.

Phase 10 must not perform long-term behavioral forecasting.

## 6. Confidence Model

Every prediction includes a confidence value bounded to:

```text
0.0 <= confidence <= 1.0
```

This value is a deterministic prediction-confidence score.

It must **not** be described as a calibrated probability unless a future certified calibration mechanism proves that interpretation.

Certified confidence bands are exactly:

```text
LOW
MEDIUM
HIGH
```

The mapping from numeric confidence to confidence band must be deterministic and versioned.

## 7. Prediction Contract

Each prediction must preserve at minimum:

```text
prediction_id
namespace_type
namespace_id
context_key
source_global_record_ids
source_phase8_record_ids
prediction_horizon
confidence
confidence_band
reason_codes
creation_sequence
predictor_id
predictor_version
```

Optional future-compatible metadata may be added only when it does not change the certified Phase 10 boundary.

## 8. Candidate Sources

Candidates may be created only from already-authorized inputs.

Certified candidate sources:

- eligible Phase 8 session-memory records
- eligible Phase 9 global-context records
- explicit current task context
- explicit execution/dependency hints already available within MERCURY

Candidate generation must never create a new memory fact.

## 9. Forbidden Candidate Sources

Phase 10 must reject or ignore:

- cross-tenant context
- cross-workspace context
- cross-project context
- expired global records
- revoked global records
- tombstoned global records
- unauthorized closed-namespace context
- unscoped global context
- hidden behavioral history
- inferred user profiles
- unrestricted external retrieval
- secrets or untraceable source material
- unsupported namespace types

## 10. Candidate Identity

Candidate identity must be deterministic.

Equivalent authorized input sets must generate the same:

- candidate IDs
- source identities
- namespace identity
- context keys
- candidate ordering

Candidate identity must not depend on:

- wall-clock time
- random values
- Python `hash()`
- filesystem ordering
- machine identity
- process identity
- network state

## 11. Feature Engine

The initial certified feature families are:

```text
RECENCY
TASK_CONTINUITY
CONTEXT_KEY_RECURRENCE
DEPENDENCY_ADJACENCY
SOURCE_LINEAGE_OVERLAP
ARTIFACT_CONTINUITY
SESSION_GLOBAL_AGREEMENT
LIFECYCLE_ELIGIBILITY
CONFLICT_STATE
HORIZON_COMPATIBILITY
```

The feature engine must remain explainable.

Each feature contribution must be:

- deterministic
- bounded
- traceable
- independently testable

Frequency alone must not imply importance.

## 12. Conflict Handling

A Phase 9 record may have:

```text
CLEAR
CONFLICTING
```

Phase 10 may predict that a conflicting context key will be needed.

It must not:

- select a winner
- suppress conflicting evidence
- rewrite evidence
- resolve the factual disagreement
- invent consensus

Prediction lineage must preserve the conflicting source identities.

Conflict may reduce confidence or emit a reason code, but the exact rule must be deterministic.

## 13. Reason Codes

Predictions must provide explicit reason codes.

Initial reason-code families may include:

```text
TASK_CONTINUITY
CONTEXT_RECURRENCE
DEPENDENCY_ADJACENCY
SOURCE_LINEAGE_OVERLAP
ARTIFACT_CONTINUITY
SESSION_GLOBAL_AGREEMENT
CONFLICT_PRESENT
NEAR_TERM_SESSION_SIGNAL
```

Reason codes must be canonicalized and bounded.

Maximum certified reason codes per prediction:

```text
MAX_REASON_CODES = 16
```

No opaque free-form explanation may be used as the certified decision basis.

## 14. Horizon Engine

The horizon engine selects exactly one of:

```text
NEXT_TURN
NEXT_TASK
SESSION_NEAR_TERM
```

The decision must be deterministic from certified features.

The horizon engine must not:

- predict long-term personal behavior
- infer user intent beyond authorized task context
- alter task execution
- initiate context retrieval
- schedule future work

## 15. Confidence Engine

The confidence engine combines certified features into a bounded score.

Requirements:

- deterministic
- reproducible
- versioned
- explanation-preserving
- bounded to [0.0, 1.0]
- no NaN
- no infinity
- no negative values
- no values above 1.0

The initial engine should prefer simple transparent weighted scoring rather than opaque learned inference.

## 16. Prediction Assembly

Prediction assembly combines:

- exact namespace
- canonical candidate
- source lineage
- selected horizon
- confidence
- confidence band
- reason codes
- predictor identity/version

It must not mutate Phase 8 or Phase 9 records.

## 17. Canonical Prediction Ordering

Predictions are ordered deterministically by:

```text
prediction_horizon
→ confidence descending
→ namespace_type
→ namespace_id
→ context_key
→ prediction_id
```

A fixed explicit ordering must exist for horizons.

No semantic/vector ranker is part of Phase 10 certification.

## 18. Certified Limits

Phase 10 locks the following limits:

```text
MAX_PREDICTION_CANDIDATES = 256
MAX_CONTEXT_PREDICTIONS = 64
MAX_SOURCE_RECORDS_PER_PREDICTION = 128
MAX_REASON_CODES = 16
```

All limits must fail closed.

## 19. Authorization Boundary

Every candidate and prediction must belong to an exact authorized namespace:

```text
(namespace_type, namespace_id)
```

No fallback is allowed between:

- tenants
- workspaces
- projects
- parent/child namespaces
- sibling namespaces

A candidate cannot borrow authorization from another source.

## 20. Namespace Closure

Closed Phase 9 namespaces must not produce new Phase 10 predictions unless an explicitly certified future policy allows read-only historical prediction.

Phase 10 baseline behavior is fail closed for closed namespaces.

## 21. Lifecycle Eligibility

Phase 9 global lifecycle handling:

- ACTIVE — eligible
- SUPERSEDED — not eligible by default for current-context prediction
- EXPIRED — forbidden
- REVOKED — forbidden
- TOMBSTONED — forbidden

Phase 8 session-memory lifecycle eligibility must follow the certified Phase 8 lifecycle rules and current-record semantics.

## 22. Source Immutability

Phase 10 must never mutate:

- Phase 8 source records
- Phase 9 global records
- provenance
- evidence
- source IDs
- namespace identity
- conflict state
- policy IDs
- session state
- global-store state

Predictions are derived outputs only.

## 23. Determinism Requirements

Equivalent inputs must produce identical:

- candidate set
- candidate IDs
- feature vectors
- horizon
- confidence
- confidence band
- reason codes
- prediction IDs
- prediction ordering
- predictor output fingerprint where applicable

Permutation of equivalent source ordering must not change certified results.

## 24. Failure Behavior

Phase 10 fails closed on:

- malformed source records
- unauthorized namespace
- closed namespace
- unknown namespace
- expired/revoked/tombstoned context
- unsupported lifecycle
- missing provenance
- missing source lineage
- invalid confidence
- unsupported horizon
- unknown confidence band
- too many candidates
- too many predictions
- too many source records per prediction
- too many reason codes
- missing predictor ID
- missing predictor version
- cross-namespace candidate aggregation
- untraceable source identity

## 25. Explicitly Forbidden Responsibilities

Phase 10 must not perform:

- memory persistence
- memory promotion
- memory deletion
- autonomous long-term retention
- context retrieval from external systems
- context prefetch
- semantic KV caching
- model selection
- model ranking
- precision selection
- hardware placement
- topology decisions
- scheduling
- runtime execution
- workload migration
- cost optimization
- latency optimization
- quality optimization
- user profiling
- personal-behavior prediction
- silent conflict resolution

## 26. Task Structure

Phase 10 is implemented in exactly seven tasks.

### Task 1 — Context Prediction Contract Baseline

Create the certified enums, contracts, limits, deterministic identity helpers, and validation rules.

Expected scope includes:

- prediction horizons
- confidence bands
- reason-code representation
- candidate contract
- feature contract
- prediction contract
- query/request/result contracts
- limit metadata

### Task 2 — Prediction Candidate Builder

Build exact-namespace prediction candidates from authorized Phase 8 and Phase 9 sources.

Must enforce:

- authorization
- lifecycle eligibility
- namespace isolation
- source traceability
- candidate limit
- deterministic candidate identity/order

### Task 3 — Deterministic Feature Engine

Extract certified explainable features from candidate/source context.

Must preserve deterministic outputs and source immutability.

### Task 4 — Horizon & Confidence Engine

Produce:

- one certified horizon
- bounded confidence
- one confidence band
- deterministic reason codes

No opaque ML dependency is required for Phase 10 baseline certification.

### Task 5 — Prediction Assembly & Ordering

Assemble final immutable predictions, enforce per-prediction source limits and global result limits, generate deterministic prediction IDs, and produce canonical ordering.

### Task 6 — Integration, Governance & Adversarial Hardening

Exercise the complete path:

```text
Phase 8 source
→ Phase 9 authorized global context
→ candidate generation
→ feature extraction
→ horizon/confidence
→ prediction assembly
→ governance checks
```

Adversarial tests cover authorization, lifecycle, closed namespaces, determinism, malformed inputs, conflicts, limits, immutability, and forbidden responsibilities.

### Task 7 — Phase 10 Certification

Create machine-readable certification configuration, fail-closed evaluator, certification tests, adversarial coverage checks, and final regression verification.

## 27. Certification Gates

Phase 10 certification must verify at minimum:

1. exact three prediction horizons
2. exact three confidence bands
3. certified limits
4. deterministic candidate identity
5. deterministic prediction identity
6. exact namespace authorization
7. tenant/workspace/project isolation
8. closed namespace rejection
9. lifecycle eligibility
10. candidate source traceability
11. source immutability
12. deterministic feature extraction
13. bounded confidence
14. deterministic confidence band
15. deterministic horizon
16. bounded canonical reason codes
17. conflict preservation
18. canonical prediction ordering
19. prediction result cap
20. per-prediction source cap
21. no semantic/vector ranking
22. no memory persistence/promotion
23. no prefetch/cache control
24. no model/hardware/scheduler/runtime control
25. no user-profile/personal-behavior prediction
26. adversarial integration coverage

The evaluator must fail closed on:

- missing gates
- failed gates
- duplicate gates
- unknown gates
- malformed gate evidence

## 28. Testing Strategy

Every implementation task follows:

```text
RED
→ verify expected failure
→ minimal GREEN
→ focused tests
→ full regression exactly once
→ checkpoint
```

Task 6 additionally includes adversarial integration tests.

Task 7 requires:

1. focused certification tests
2. certification evaluator PASS
3. final full regression
4. clean Git status
5. final certification commit

## 29. Non-Goals

Phase 10 does not attempt to solve:

- long-term behavioral prediction
- semantic search
- embedding retrieval
- vector databases
- cache placement
- runtime prefetch
- distributed execution
- model-routing policy
- hardware forecasting
- workload scheduling
- autonomous resource allocation

These remain outside the Phase 10 certified boundary.

## 30. Completion Definition

Phase 10 is complete only when:

- all seven tasks are checkpointed
- all certified prediction contracts are deterministic
- authorization and lifecycle boundaries fail closed
- source immutability is proven
- predictions remain explainable
- certification evaluator returns PASS
- full regression is green
- final Git status is clean

At that point MERCURY X may proceed to Phase 11 — Semantic KV Cache.
