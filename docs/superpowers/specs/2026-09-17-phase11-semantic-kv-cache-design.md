# MERCURY X — Phase 11 Semantic KV Cache Design

Date: 2026-09-17  
Status: Approved architecture  
Phase: 11 — Semantic KV Cache

## 1\. Purpose

Phase 11 determines whether previously computed authorized semantic context or model-specific KV-state artifacts are safe to reuse.

It provides:

* deterministic cache identity
* exact namespace isolation
* semantic-context reuse metadata
* strict physical KV compatibility checks
* backend-neutral payload references
* lifecycle and invalidation controls
* bounded lookup
* source lineage and provenance
* integration with Phase 10 predictions

Phase 11 does **not** decide where or when computation executes.

## 2\. Position in MERCURY X

```text
Phase 8 Session Memory
        +
Phase 9 Global Context Memory
        +
Phase 10 Context Prediction
        ↓
Semantic KV Cache Lookup
        ↓
Compatibility / Reuse Guard
        ↓
Reuse Decision
        ↓
Semantic Context Entry
        +
Optional Physical KV Payload Reference
        ↓
Later Phase 12+ execution systems
```

Phase 11 is a control-plane cache subsystem. Physical KV storage may live in an external backend.

## 3\. Fundamental Rule

> Phase 11 decides whether previously computed authorized context/KV artifacts are safely reusable; it does not decide where or when computation executes.

## 4\. Reuse Modes

Phase 11 supports exactly:

```text
EXACT
SEMANTIC\_COMPATIBLE
NO\_REUSE
```

### EXACT

The requested cache identity and all certified compatibility fields match exactly.

### SEMANTIC\_COMPATIBLE

The higher-level semantic context is reusable, but physical KV tensors may only be reused if all physical compatibility constraints also match.

### NO\_REUSE

Reuse is unsafe, unauthorized, incompatible, invalidated, stale, or otherwise uncertified.

## 5\. Cache Entry States

Phase 11 supports exactly:

```text
ACTIVE
STALE
INVALIDATED
```

### ACTIVE

Eligible for reuse subject to compatibility and authorization.

### STALE

Retained for lineage/audit but excluded from current reuse by default.

### INVALIDATED

Explicitly invalidated and forbidden from reuse.

## 6\. Semantic vs Physical KV Reuse

Phase 11 distinguishes two classes of reuse.

### 6.1 Semantic Context Reuse

May reuse higher-level context artifacts when semantic identity and authorization rules permit.

Examples include:

* normalized context representation
* summarized reusable context
* tokenized context artifact metadata
* deterministic preprocessed context
* reusable semantic context fingerprints

### 6.2 Physical KV Tensor Reuse

Physical transformer KV-state reuse is stricter.

Semantic similarity alone is **never** sufficient.

Physical KV reuse requires certified compatibility across at least:

```text
model\_id
model\_version
tokenizer\_id
attention\_layout
kv\_format
precision
context\_generation
namespace\_type
namespace\_id
```

Any mismatch forces physical KV `NO\_REUSE`.

## 7\. Backend-Neutral Physical Payload References

CPU-first development must not require CUDA or a local GPU.

Physical payloads are represented by:

```text
payload\_backend
payload\_reference
payload\_fingerprint
payload\_size\_bytes
```

The baseline implementation stores metadata and references only.

Actual payload backends may later include:

* local test backend
* vLLM KV backend
* Triton-backed service
* GPU memory manager
* remote cache service
* disaggregated memory service

Phase 11 contracts must not depend on a specific backend.

## 8\. Certified Compatibility Identity

Each cache entry must include or derive:

```text
namespace\_type
namespace\_id
cache\_entry\_id
cache\_generation
semantic\_key
semantic\_fingerprint
model\_id
model\_version
tokenizer\_id
attention\_layout
kv\_format
precision
context\_generation
source\_phase8\_record\_ids
source\_global\_record\_ids
source\_prediction\_ids
source\_artifact\_ids
payload\_backend
payload\_reference
payload\_fingerprint
payload\_size\_bytes
state
creation\_sequence
invalidation\_reason
```

Fields not applicable to semantic-only entries must be represented explicitly and deterministically.

## 9\. Deterministic Cache Identity

Equivalent inputs must generate identical cache IDs and fingerprints.

Identity must not depend on:

* wall-clock time
* random UUIDs
* Python `hash()`
* filesystem ordering
* process identity
* machine identity
* network state

Use canonical JSON + SHA-256.

## 10\. Certified Limits

```text
MAX\_KV\_CACHE\_ENTRIES\_PER\_NAMESPACE = 4096
MAX\_CACHE\_LOOKUP\_RESULTS = 64
MAX\_SOURCE\_RECORDS\_PER\_CACHE\_ENTRY = 128
MAX\_CACHE\_DEPENDENCIES = 64
MAX\_CACHE\_METADATA\_BYTES = 65536
```

All limits fail closed.

## 11\. Namespace Authorization

Every lookup, admission, reuse decision, and invalidation is scoped to exact:

```text
(namespace\_type, namespace\_id)
```

No fallback is allowed across:

* tenant
* workspace
* project
* sibling namespace
* parent/child namespace

Phase 11 must never search a broader scope when an exact namespace misses.

## 12\. Source Lineage

Every cache entry preserves exact source lineage.

Sources may include:

* Phase 8 session-memory record IDs
* Phase 9 global-context record IDs
* Phase 10 prediction IDs
* source artifacts

Lineage must remain canonical, immutable, deduplicated, and bounded.

## 13\. Semantic Identity

Semantic identity must be deterministic and explainable.

The baseline design does not require embeddings.

A semantic cache key may derive from certified structured context such as:

```text
namespace
context key
source lineage
normalized context representation
artifact lineage
context generation
```

If embedding/vector semantics are introduced later, they must not bypass authorization or physical KV compatibility checks.

## 14\. Exact Reuse Guard

`EXACT` reuse requires exact match of:

```text
namespace
semantic key
model\_id
model\_version
tokenizer\_id
attention\_layout
kv\_format
precision
context\_generation
payload fingerprint when physical payload exists
```

An exact cache hit still fails closed if lifecycle, invalidation, namespace, or lineage checks fail.

## 15\. Semantic Compatibility Guard

`SEMANTIC\_COMPATIBLE` may be returned for higher-level semantic reuse when certified semantic identity is compatible.

It must not imply physical KV compatibility.

The result must explicitly state whether:

```text
semantic\_reuse\_allowed
physical\_kv\_reuse\_allowed
```

These are separate decisions.

## 16\. Phase 10 Prediction Integration

Phase 10 predicts which authorized context may be needed next.

Phase 11 may use Phase 10 prediction IDs as lookup hints.

Phase 10 output may influence cache lookup priority, but it must not:

* force a hit
* override authorization
* override lifecycle
* override physical compatibility
* override invalidation
* create cache entries autonomously

Prediction is a hint, not authority.

## 17\. Cache Lookup

Lookup must be deterministic, bounded, and structured.

The baseline lookup should support:

* exact namespace
* semantic key
* source prediction ID
* model identity
* tokenizer identity
* precision
* context generation
* state
* backend availability metadata

Canonical result ordering:

```text
reuse\_mode
→ semantic\_key
→ model\_id
→ model\_version
→ context\_generation
→ creation\_sequence
→ cache\_entry\_id
```

No uncontrolled semantic ranking is part of baseline certification.

## 18\. Cache Store

The Phase 11 store must:

* isolate namespaces
* enforce per-namespace cap
* preserve immutable cache entry identity
* reject duplicate/conflicting registrations
* support deterministic fingerprints
* preserve invalidated/stale entries for audit
* reject unauthorized writes
* reject writes into closed namespaces when Phase 9 governance says the namespace is closed

## 19\. Cache Admission

New cache entries require explicit admission.

Admission must validate:

* exact namespace authorization
* source lineage
* entry state
* semantic identity
* physical compatibility metadata if physical payload exists
* payload reference/fingerprint consistency
* metadata-size limit
* source-record limit
* dependency limit
* namespace capacity

Phase 11 must not auto-admit entries solely because a prediction exists.

## 20\. Invalidation

Invalidation is explicit and immutable.

Invalidating an entry must:

* preserve the prior entry
* create deterministic invalidation metadata
* prevent future reuse
* preserve reason
* preserve source lineage
* preserve payload fingerprint/reference metadata for audit unless policy requires redaction at another layer

Invalidation must never silently delete lineage.

## 21\. Staleness

Entries may become `STALE`.

Staleness means:

* retained
* auditable
* not selected for current reuse by default

A stale entry may not return `EXACT` or physical reuse unless a future explicitly certified policy allows it.

Baseline Phase 11 excludes stale entries from current reuse.

## 22\. Dependency Tracking

Cache entries may declare dependencies.

Examples:

* upstream semantic context entries
* source artifacts
* model generation
* tokenizer generation
* context generation

Maximum dependencies:

```text
MAX\_CACHE\_DEPENDENCIES = 64
```

Dependency invalidation must propagate only through explicit dependency relationships.

No broad heuristic invalidation.

## 23\. Metadata Size

Serialized cache metadata is capped at:

```text
MAX\_CACHE\_METADATA\_BYTES = 65536
```

The check must use deterministic canonical serialization.

Oversized metadata fails closed.

## 24\. Physical Payload Safety

Physical payload references must never be trusted solely because a cache entry exists.

A payload reference must include:

```text
payload\_backend
payload\_reference
payload\_fingerprint
payload\_size\_bytes
```

If any required physical payload field is malformed or incomplete, physical KV reuse is forbidden.

Semantic reuse may still be considered independently if safe.

## 25\. Precision Compatibility

Physical KV reuse requires exact precision compatibility.

Examples:

```text
FP32 != FP16
FP16 != BF16
INT8 != FP16
```

Phase 11 must not silently cast or reinterpret KV tensors.

Precision conversion belongs to a later execution/runtime responsibility if ever supported.

## 26\. Tokenizer Compatibility

Physical KV reuse requires exact tokenizer identity.

A tokenizer mismatch forces:

```text
physical\_kv\_reuse\_allowed = False
```

Even when semantic context is otherwise equivalent.

## 27\. Model Compatibility

Physical KV reuse requires exact model identity/version unless a future certified compatibility matrix explicitly allows otherwise.

The baseline is exact-only.

No cross-model physical KV reuse.

## 28\. Attention Layout / KV Format Compatibility

Physical reuse requires exact match for:

```text
attention\_layout
kv\_format
```

Examples of incompatible differences may include:

* head layout
* grouped-query attention layout
* KV packing format
* block layout
* backend-specific representation

Phase 11 does not attempt conversion.

## 29\. Context Generation

`context\_generation` identifies the generation/version of the prepared context/KV state.

Physical reuse requires exact generation match.

Semantic reuse may allow compatible generations only through explicit certified rules.

Baseline: exact generation for physical reuse.

## 30\. Failure Behavior

Phase 11 fails closed on:

* unauthorized namespace
* closed namespace
* invalid lifecycle/state
* malformed cache entry
* malformed semantic identity
* malformed physical compatibility metadata
* invalid payload reference
* missing payload fingerprint
* invalid payload size
* unknown model identity
* unknown tokenizer identity
* unsupported precision
* unsupported attention layout
* unsupported KV format
* unsupported reuse mode
* unsupported entry state
* cross-namespace dependency
* untraceable source lineage
* excessive source records
* excessive dependencies
* excessive metadata size
* namespace capacity overflow
* invalidated entry reuse
* stale entry current reuse
* conflicting duplicate cache identity

## 31\. Forbidden Responsibilities

Phase 11 must not:

* select a model
* rank models
* select precision
* convert precision
* allocate hardware
* choose GPU/CPU
* select topology
* schedule execution
* migrate workloads
* execute inference
* preempt workloads
* optimize cost
* optimize latency globally
* perform workload placement
* resolve Phase 9 factual conflicts
* modify Phase 10 prediction confidence
* create user profiles
* perform personal-behavior prediction

## 32\. CPU-First Development

All Phase 11 control-plane behavior must run on CPU-only development machines.

Local tests use metadata and optional small fake payload references.

GPU-dependent backend validation is deferred to modular backend adapters and cloud/free GPU environments when needed.

The architecture must remain capable of real physical KV backends without requiring one for baseline certification.

## 33\. Task Structure

Phase 11 uses exactly eight tasks.

### Task 1 — Semantic KV Cache Contract Baseline

Create:

* certified enums
* limits
* cache-entry contracts
* lookup request/result contracts
* compatibility result
* deterministic identity helpers
* payload-reference contracts
* dependency contracts

### Task 2 — Deterministic Semantic Cache Identity

Implement:

* semantic keys
* canonical payloads
* deterministic cache IDs
* metadata fingerprints
* permutation invariance
* metadata-size enforcement

### Task 3 — Compatibility \& Reuse Guard

Implement:

* exact compatibility
* semantic compatibility
* physical KV compatibility
* model/tokenizer/precision/layout/format/context-generation checks
* explicit semantic vs physical reuse booleans

### Task 4 — Cache Store \& Namespace Isolation

Implement:

* immutable cache registration
* exact namespace isolation
* namespace cap
* closed-namespace rejection
* deterministic store fingerprint
* duplicate/conflicting identity handling

### Task 5 — Lookup, Matching \& Prediction Integration

Implement:

* exact structured lookup
* bounded result count
* canonical ordering
* Phase 10 prediction hint integration
* no prediction override of safety rules

### Task 6 — Lifecycle, Invalidation \& Eviction Policy

Implement:

* ACTIVE
* STALE
* INVALIDATED
* deterministic invalidation
* dependency-aware invalidation
* explicit bounded eviction policy metadata
* no heuristic silent deletion

Baseline eviction decisions must remain deterministic and local to the cache store. Global compute/resource placement remains out of scope.

### Task 7 — Integration \& Adversarial Hardening

Exercise:

```text
Phase 10 prediction
→ Phase 11 lookup
→ compatibility guard
→ reuse decision
→ lifecycle/invalidation
```

Test exact namespace boundaries, physical compatibility, semantic-only reuse, backend references, limits, dependency propagation, immutability, and forbidden responsibilities.

### Task 8 — Phase 11 Certification

Create:

* `configs/certification/phase11.json`
* `src/mercury/certification/phase11.py`
* `tests/test\_phase11\_certification.py`

Certification must fail closed.

## 34\. Certification Gates

Phase 11 certification must verify at minimum:

1. exact reuse modes
2. exact cache entry states
3. certified limits
4. deterministic semantic identity
5. deterministic cache entry identity
6. metadata-size bound
7. exact namespace authorization
8. tenant/workspace/project isolation
9. closed namespace rejection
10. source lineage preservation
11. exact compatibility
12. semantic compatibility separation
13. physical KV compatibility separation
14. model identity enforcement
15. model version enforcement
16. tokenizer identity enforcement
17. precision enforcement
18. attention layout enforcement
19. KV format enforcement
20. context generation enforcement
21. payload-reference validation
22. payload fingerprint validation
23. store capacity bound
24. lookup result bound
25. source-record bound
26. dependency bound
27. canonical lookup ordering
28. stale exclusion
29. invalidated exclusion
30. deterministic invalidation
31. dependency-aware invalidation
32. prediction integration is hint-only
33. no semantic-only physical KV reuse
34. no model selection
35. no precision selection/conversion
36. no hardware placement
37. no scheduling/runtime execution
38. no user-profile/personal-behavior prediction
39. adversarial integration coverage

## 35\. Testing Strategy

Every implementation task follows:

```text
RED
→ verify expected failure
→ minimal GREEN
→ focused tests
→ full regression once
→ checkpoint
```

For fast-track execution, closely related files may be delivered in one downloadable bundle, but verification must still be explicit and failures must be corrected with full-file replacements rather than partial patches.

## 36\. Completion Definition

Phase 11 is complete only when:

* all eight tasks are implemented
* focused tests are green
* certification evaluator returns PASS
* final full regression is green
* Git working tree is clean
* Phase 10 compatibility remains intact
* Phase 12 can consume Phase 11 through stable contracts without changing Phase 11 semantics

At completion, MERCURY X proceeds to Phase 12 — Disaggregated Cognitive Execution.

