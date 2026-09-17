# MERCURY X — Phase 8 Agent Session Memory Fabric Design

**Date:** 2026-09-17
**Status:** Locked design
**Phase:** 8 — Agent Session Memory Fabric

## Objective
Phase 8 manages short-lived, session-scoped memory for AI execution. It decides what execution artifacts may be retained during an active session, how they are identified, stored, retrieved, compacted, expired, tombstoned, and isolated.

It does not implement long-term global memory, user-profile memory, cross-session memory, model selection, hardware placement, scheduling, or runtime execution.

## Certified Baseline
Memory types exactly:
- OBSERVATION
- INTERMEDIATE_RESULT
- TOOL_RESULT
- DECISION_CONTEXT
- EXECUTION_STATE
- COMPACTED_SUMMARY

Scopes exactly:
- TURN
- TASK
- SESSION

Forbidden scopes:
- GLOBAL
- USER_PROFILE
- CROSS_SESSION

Lifecycle states exactly:
- ACTIVE
- COMPACTED
- EXPIRED
- TOMBSTONED

Phase result states exactly:
- READY
- NOT_APPLICABLE
- FAIL

## Identity
Every record preserves:
- session_id
- task_id
- turn_id
- record_id
- record_version
- source_phase
- source_artifact_id
- memory_type
- scope
- creation_sequence
- retention/expiry metadata
- lifecycle state
- provenance/evidence

Record identity is deterministic and collision-resistant.

## Components
1. Session Memory Contracts
2. Memory Admission Engine
3. Session Memory Store
4. Memory Retrieval Engine
5. Memory Compaction Engine
6. Lifecycle & Isolation Engine
7. Phase 8 Certification Layer

## Admission
An artifact is admissible only when:
- session_id exactly matches the active session
- memory type and scope are certified
- artifact is explicitly retainable
- explicit secret/credential classification is absent
- retention is bounded
- provenance is complete
- source artifact identity is valid
- duplicate identity is either semantically identical or rejected
- no forbidden global/profile/cross-session scope exists

No free-form guessing decides admission.

## Store
The store:
- partitions strictly by session
- preserves immutable record versions
- registers deterministically
- rejects conflicting duplicate IDs
- excludes expired/tombstoned records from active reads
- fails closed on unknown lifecycle state
- enforces MAX_SESSION_MEMORY_RECORDS = 1024

## Retrieval
Certified retrieval uses structured deterministic filters:
- exact session
- task ID
- turn range
- memory type
- scope
- source artifact/lineage
- explicit retrieval key
- lifecycle state

Canonical ordering:
session_id → task_id → turn_id → creation_sequence → record_id

MAX_RETRIEVED_RECORDS = 64.

Caller limits may be smaller positive values only. Expired/tombstoned records are excluded from normal active retrieval.

## Compaction
Compaction is structure-preserving. A compacted record preserves:
- source record IDs
- source record versions
- source provenance
- compaction method ID/version
- target session/task scope
- deterministic summary identity

MAX_COMPACTION_INPUT_RECORDS = 128.

Compaction must not cross sessions, erase lineage, or create opaque untraceable summaries.

## Lifecycle
Allowed transitions:
- ACTIVE → COMPACTED
- ACTIVE → EXPIRED
- ACTIVE → TOMBSTONED
- COMPACTED → EXPIRED
- COMPACTED → TOMBSTONED

Forbidden:
- terminal state → ACTIVE
- payload mutation after expiry/tombstone
- cross-session lifecycle transition
- unbounded retention extension
- admission after session closure

## Session Closure
On session closure:
- no new records are admitted
- no active record is mutated
- closure policy is applied deterministically
- required expiry/tombstone transitions occur
- cross-session reuse remains forbidden

## Secret Handling
Explicitly classified credentials, passwords, API keys/tokens, authentication secrets, and private key material are rejected from admission.

Phase 8 does not perform guessed secret detection from arbitrary free-form text.

## Determinism
Record IDs use stable SHA-256 canonical logical content.

IDs must not depend on random UUIDs, Python hash(), filesystem order, machine state, or unstable provenance ordering.

## Limits
- MAX_SESSION_MEMORY_RECORDS = 1024
- MAX_RETRIEVED_RECORDS = 64
- MAX_COMPACTION_INPUT_RECORDS = 128

Zero, negative, unknown, or above-certified limits fail closed.

## Fail-Closed Rules
Reject/fail on:
- cross-session access/write
- unknown type/scope/lifecycle
- forbidden global/profile/cross-session scope
- expired/tombstoned record returned as active
- conflicting duplicate identity
- missing provenance/source identity
- unbounded retention
- secret/credential admission
- session-closed mutation
- retrieval/compaction cap violation
- compaction without source lineage
- malformed record
- unsupported schema
- hidden long-term/global/profile memory leakage

No automatic repair, silent scope escalation, or cross-session fallback.

## Forbidden Behavior
Phase 8 must not expose or perform:
- global memory creation
- user-profile memory creation
- cross-session memory reuse
- model selection
- hardware/device placement
- scheduling
- runtime execution
- autonomous long-term retention
- cost/latency/quality optimization

## Immutability and Provenance
Do not mutate upstream execution artifacts, Phase 5 compositions, Phase 6 precision profiles, Phase 7 morph profiles, source provenance, policy objects, or immutable record versions.

Every final memory artifact remains traceable to session/task/turn, source phase/artifact, admission decision, lifecycle state, compaction lineage, and policy/evidence.

## Testing Strategy
Cover:
- exact vocabularies and immutability
- deterministic IDs
- admission and secret rejection
- strict session isolation
- duplicate/conflict handling
- deterministic retrieval
- all certified limits
- expired/tombstoned exclusion
- traceable compaction
- lifecycle transitions
- session closure
- integration failures
- hidden global/profile leakage
- certification

## Implementation Tasks
1. Session Memory Contract Baseline
2. Memory Admission & Session Store
3. Session Memory Retrieval Engine
4. Memory Compaction Engine
5. Lifecycle, Expiry & Isolation Engine
6. Integration & Failure Hardening
7. Phase 8 Certification

## Exit Criteria
Phase 8 is complete only when:
- exactly six memory types are certified
- exactly three scopes are certified
- exactly four lifecycle states are certified
- session isolation is proven
- deterministic IDs/order are proven
- all three limits are enforced
- compaction preserves source lineage
- expired/tombstoned records are excluded correctly
- session closure is enforced
- no cross-session leakage exists under certified paths
- no global/user-profile memory behavior exists
- adversarial integration passes
- certification passes
- full repository regression passes
