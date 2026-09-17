# MERCURY X — Phase 12 Disaggregated Cognitive Execution Design

Date: 2026-09-17
Status: Approved architecture
Phase: 12 — Disaggregated Cognitive Execution

## 1\. Purpose

Phase 12 decomposes an AI workload into independently executable segments connected through explicit, authorized, verifiable handoff contracts.

It defines:

* execution segments
* segment dependencies
* segment inputs/outputs
* legal handoffs between segments
* readiness conditions
* failure/retry metadata
* verification metadata
* deterministic result stitching

Phase 12 does not decide where computation runs.

## 2\. Position in MERCURY X

```text
Phase 3 AI Execution Graph
        +
Phase 10 Context Prediction
        +
Phase 11 Semantic KV Cache
        ↓
Disaggregation Planner
        ↓
Execution Segment Graph
        ↓
Boundary / Handoff Contracts
        ↓
Segment Readiness Engine
        ↓
Runtime Adapter Boundary
        ↓
Verification
        ↓
Result Stitching
```

## 3\. Fundamental Rule

> A downstream segment cannot execute unless every required upstream handoff is authorized, available, compatible, and verified.

## 4\. Architectural Boundary

Phase 12 owns:

* execution segmentation
* segment dependency contracts
* segment readiness
* handoff contracts
* handoff state
* execution state
* retry metadata
* verification metadata
* deterministic result stitching

Phase 12 does not own:

* model selection
* precision selection
* hardware selection
* provider selection
* region selection
* placement
* topology optimization
* global scheduling
* workload migration
* global cost/latency optimization

## 5\. Certified Segment Types

Exactly:

```text
PREFILL
DECODE
TOOL\_EXECUTION
RETRIEVAL
TRANSFORM
AGGREGATION
```

No arbitrary unbounded segment type is part of the certified baseline.

## 6\. Execution Segment Contract

Each segment contains at minimum:

```text
segment\_id
execution\_plan\_id
segment\_type
input\_artifact\_ids
output\_contract\_id
model\_requirement\_id
context\_requirement\_id
kv\_requirement\_id
dependency\_segment\_ids
required\_handoff\_ids
produced\_handoff\_ids
handoff\_policy\_id
retry\_policy\_id
verification\_policy\_id
creation\_sequence
execution\_state
```

## 7\. Certified Execution States

Exactly:

```text
PLANNED
READY
RUNNING
SUCCEEDED
FAILED
CANCELLED
```

PLANNED means declared but not executable yet.
READY means all certified prerequisites pass.
RUNNING means execution started.
SUCCEEDED means execution completed and verification passed.
FAILED means execution failed.
CANCELLED means explicitly cancelled and terminal.

## 8\. Certified Handoff Kinds

Exactly:

```text
ARTIFACT
CONTEXT
KV\_REFERENCE
CONTROL
```

## 9\. Certified Handoff States

Exactly:

```text
PENDING
AVAILABLE
CONSUMED
INVALIDATED
```

## 10\. Execution Plan

The primary Phase 12 object is the Disaggregated Execution Plan.

It contains:

```text
execution\_plan\_id
source\_execution\_graph\_id
segments
handoffs
entry\_segment\_ids
terminal\_segment\_ids
creation\_sequence
plan\_version
plan\_fingerprint
```

The plan must be deterministic, acyclic, namespace-safe, bounded, traceable, and immutable after admission.

## 11\. Deterministic Identity

Equivalent inputs must produce identical:

* execution plan IDs
* segment IDs
* handoff IDs
* plan fingerprints
* canonical ordering
* result-stitching IDs

Identity must not depend on wall-clock time, random UUIDs, Python hash(), machine/process identity, filesystem ordering, or network state.

Use canonical JSON + SHA-256.

## 12\. Certified Limits

```text
MAX\_SEGMENTS\_PER\_EXECUTION\_PLAN = 256
MAX\_DEPENDENCIES\_PER\_SEGMENT = 64
MAX\_HANDOFFS\_PER\_SEGMENT = 64
MAX\_EXECUTION\_ARTIFACTS\_PER\_SEGMENT = 128
MAX\_RETRY\_ATTEMPTS = 8
```

All limits fail closed.

## 13\. Segment Graph Rules

The dependency graph must:

* be acyclic
* contain only declared segment IDs
* reject self-dependency
* reject duplicate dependency edges
* reject dangling dependencies
* reject duplicate segment IDs
* have at least one entry segment
* have at least one terminal segment
* have deterministic canonical ordering

## 14\. Dependency Semantics

A segment is dependency-ready only when:

* every upstream dependency exists
* every upstream dependency succeeded
* all required handoffs are AVAILABLE
* all handoffs are authorized
* all compatibility checks pass
* all required verification passes

Dependency edges alone do not make a segment ready.

## 15\. Handoff Contract

Each handoff includes:

```text
handoff\_id
execution\_plan\_id
producer\_segment\_id
consumer\_segment\_id
handoff\_kind
payload\_reference
payload\_fingerprint
authorization\_scope
compatibility\_contract\_id
verification\_contract\_id
state
creation\_sequence
invalidation\_reason
```

No handoff may cross undeclared namespace boundaries.

## 16\. KV Reference Integration

Phase 12 integrates with Phase 11 through `KV\_REFERENCE` handoffs.

A KV handoff preserves:

* Phase 11 cache entry ID
* semantic/cache identity
* payload fingerprint when present
* model/tokenizer/KV compatibility identity
* namespace identity
* context generation
* cache state compatibility

Phase 12 must not override Phase 11 compatibility decisions.

## 17\. Context Integration

Phase 10 predictions and authorized context references may be linked through CONTEXT handoffs.

Phase 12 must not:

* create long-term memory
* change Phase 10 confidence
* change Phase 9 truth/conflict state
* widen namespace authorization

## 18\. Runtime Adapter Boundary

Phase 12 may expose a backend-neutral runtime adapter contract conceptually equivalent to:

```text
execute\_segment(segment, resolved\_inputs) -> segment\_execution\_result
```

Possible adapters may later include CPU test, subprocess, remote service, GPU runtime, tool execution, or retrieval adapters.

Phase 12 does not choose which adapter/provider is optimal.

## 19\. Resource Requirements vs Placement

A segment may declare requirements such as:

```text
requires\_gpu
minimum\_memory\_bytes
supported\_accelerator\_classes
network\_locality\_required
requires\_external\_tool\_access
requires\_retrieval\_access
```

These are declarative only. Phase 12 does not perform placement.

## 20\. Readiness Engine

PLANNED → READY requires:

* dependencies succeeded
* required handoffs AVAILABLE
* authorization passes
* compatibility passes
* verification prerequisites pass
* retry state allows execution
* segment is not cancelled

Readiness must be deterministic.

## 21\. Execution State Transition Matrix

Allowed baseline transitions:

```text
PLANNED → READY
READY → RUNNING
RUNNING → SUCCEEDED
RUNNING → FAILED
PLANNED → CANCELLED
READY → CANCELLED
RUNNING → CANCELLED
FAILED → READY
```

`FAILED → READY` is permitted only under a certified retry policy.

Forbidden examples:

```text
SUCCEEDED → RUNNING
CANCELLED → READY
CANCELLED → RUNNING
SUCCEEDED → FAILED
```

## 22\. Retry Policy

Retry-capable segments define:

* max attempts
* retryable failure categories
* deterministic attempt sequence
* no infinite retries
* timing/backoff metadata without wall-clock dependency in tests

Maximum:

```text
MAX\_RETRY\_ATTEMPTS = 8
```

## 23\. Failure Categories

Exactly:

```text
INPUT\_FAILURE
HANDOFF\_FAILURE
COMPATIBILITY\_FAILURE
RUNTIME\_FAILURE
VERIFICATION\_FAILURE
CANCELLED\_FAILURE
```

## 24\. Verification

A segment may only transition to SUCCEEDED when its configured verification contract passes.

Verification may include:

* artifact fingerprint validation
* output schema validation
* handoff completeness
* provenance validation
* Phase 11 payload integrity
* deterministic output identity where applicable

Unverifiable output fails closed.

## 25\. Result Stitching

Terminal outputs are combined deterministically.

The stitched result preserves:

```text
execution\_plan\_id
terminal\_segment\_ids
terminal\_result\_ids
artifact\_lineage
verification\_status
stitching\_policy\_id
result\_fingerprint
```

Missing required terminal outputs cause failure.

## 26\. Cancellation

Cancellation is explicit and auditable.

A cancelled segment:

* cannot become READY/RUNNING
* cannot create new AVAILABLE handoffs
* cannot be retried
* remains auditable

Propagation follows declared control/dependency rules only.

## 27\. Handoff Consumption

AVAILABLE handoffs may become CONSUMED only by the declared authorized consumer.

No unrelated segment may consume them.

## 28\. Handoff Invalidation

Invalidation is explicit and terminal for that handoff instance.

Reasons may include:

* upstream invalidation
* compatibility failure
* verification failure
* cancellation policy
* source cache/context revocation

Reason and lineage must be preserved.

## 29\. Namespace Isolation

Every plan, segment, handoff, and result belongs to an exact authorized namespace.

No fallback across tenant, workspace, project, parent/child, or sibling scopes.

## 30\. Closed Namespace Behavior

If the relevant Phase 9 namespace is closed:

* no new plan may be admitted
* no new segment may start
* no new handoff may be created
* historical metadata may remain auditable

Baseline behavior is fail closed.

## 31\. Phase 11 Cache-State Interaction

KV\_REFERENCE must reject Phase 11 entries that are:

```text
STALE
INVALIDATED
```

Baseline allows only ACTIVE compatible cache references.

## 32\. Phase 10 Prediction Interaction

Phase 10 predictions may inform expected context/KV handoffs, but may not:

* create segments automatically
* widen authorization
* override readiness
* override verification
* force physical KV reuse
* force execution

Prediction remains advisory.

## 33\. Input Immutability

Phase 12 must not mutate Phase 3, Phase 9, Phase 10, Phase 11, or source artifact objects.

Derived Phase 12 objects are new immutable control-plane records.

## 34\. CPU-First Development

All control-plane behavior must run on CPU-only machines.

Baseline certification does not require CUDA, Triton, vLLM, multi-GPU, RDMA, or distributed GPU hardware.

GPU execution remains an adapter/backend concern.

## 35\. Forbidden Responsibilities

Phase 12 must not:

* select/rank models
* choose/convert precision
* select hardware/provider/region/topology
* schedule workloads globally
* migrate/rebalance workloads
* negotiate cost
* optimize fleet utilization
* scale infrastructure
* create user profiles
* predict personal behavior

## 36\. Task Structure

Exactly eight tasks:

1. Disaggregated Execution Contract Baseline
2. Execution Segment Graph Builder
3. Handoff Contract \& State Engine
4. Segment Readiness \& Dependency Engine
5. Phase 11 KV / Context Integration
6. Failure, Retry \& Result Stitching
7. Integration \& Adversarial Hardening
8. Phase 12 Certification

## 37\. Certification Gates

At minimum verify:

1. exact segment types
2. exact execution states
3. exact handoff kinds
4. exact handoff states
5. certified limits
6. deterministic segment identity
7. deterministic handoff identity
8. deterministic plan identity
9. deterministic plan fingerprint
10. acyclic dependency graph
11. self-dependency rejection
12. dangling dependency rejection
13. duplicate segment rejection
14. entry/terminal identification
15. exact namespace authorization
16. namespace isolation
17. closed namespace rejection
18. handoff producer/consumer validation
19. handoff state transition matrix
20. readiness dependency enforcement
21. readiness handoff enforcement
22. execution state transition matrix
23. cancellation terminal behavior
24. retry limit
25. retry eligibility
26. failure classification
27. KV reference compatibility
28. stale/invalidated KV rejection
29. Phase 10 prediction hint-only behavior
30. source immutability
31. verification-before-success
32. deterministic result stitching
33. missing terminal result failure
34. result lineage preservation
35. no model selection
36. no precision selection
37. no hardware/provider/region placement
38. no global scheduling
39. no migration
40. no user-profile/personal-behavior prediction
41. adversarial integration coverage

## 38\. Testing Strategy

Every task follows:

```text
RED
→ verify expected failure
→ minimal GREEN
→ focused tests
→ full regression once
→ checkpoint
```

Fast-track delivery may batch related files, but final verification still requires:

* focused Phase 12 suite
* certification evaluator PASS
* final full regression
* clean Git status

## 39\. Completion Definition

Phase 12 is complete only when:

* all eight tasks are implemented
* all focused tests pass
* certification returns PASS
* full MERCURY regression is green
* working tree is clean
* Phase 10 and Phase 11 remain compatible
* no placement/scheduler/runtime responsibility leaks into Phase 12

After Phase 12 certification, perform the previously planned Phase 10 hardening pass before continuing significantly further in the roadmap.

