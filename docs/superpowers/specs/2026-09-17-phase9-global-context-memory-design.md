# MERCURY X — Phase 9 Global Context Memory Design

**Date:** 2026-09-17
**Status:** Locked design
**Phase:** 9 — Global Context Memory

## Objective
Phase 9 preserves reusable context across authorized sessions without creating uncontrolled personal profiling or unconstrained global visibility. Phase 8 owns active-session memory; Phase 9 owns explicitly promoted, persistent, namespace-scoped context.

Core flow:

Phase 8 Session Memory → Promotion Request → Promotion Eligibility → Namespace Authorization → Global Context Record → Versioned Global Store → Bounded Retrieval → Consolidation / Conflict Handling → Governance & Retention

## Certified Global Memory Types
Exactly six:
- PROJECT_CONTEXT
- WORKSPACE_CONTEXT
- EXECUTION_KNOWLEDGE
- VALIDATED_FACT
- REUSABLE_ARTIFACT_CONTEXT
- GLOBAL_SUMMARY

## Certified Namespaces
Exactly three:
- TENANT
- WORKSPACE
- PROJECT

No unrestricted USER_PROFILE namespace is certified.

## Lifecycle States
Exactly five:
- ACTIVE
- SUPERSEDED
- EXPIRED
- REVOKED
- TOMBSTONED

## Conflict States
Exactly:
- CLEAR
- CONFLICTING

## Phase Result States
Exactly:
- READY
- NOT_APPLICABLE
- FAIL

## Global Record Identity
Every record preserves at minimum: schema version, namespace type, namespace ID, global record ID, record version, source session ID, source Phase 8 record IDs, source artifact IDs, source phase, global memory type, context key, creation sequence, lifecycle state, conflict state, provenance/evidence, promotion policy ID, retention policy ID, supersedes record ID when applicable, and change reason when versioned.

IDs are deterministic SHA-256 digests over canonical logical content.

## Promotion Model
Global memory may be created only through explicit promotion. Required checks:
1. source is valid Phase 8 memory;
2. promotion explicitly requested;
3. target namespace is certified;
4. caller is authorized for that namespace;
5. source provenance is complete;
6. retention policy is explicit;
7. artifact is explicitly persistable;
8. secrets/credentials are rejected;
9. malformed or unresolved source state fails closed;
10. source lineage remains traceable.

No promotion based on frequency, model guess, perceived importance, hidden heuristic, or implicit long-term retention.

## Global Context Store
Strict namespace partitioning, deterministic registration, immutable versions, duplicate/conflict detection, supersession lineage, lifecycle-aware reads, exact namespace authorization, bounded storage.

`MAX_GLOBAL_RECORDS_PER_NAMESPACE = 4096`

## Retrieval
Structured deterministic filters: namespace type/ID, memory type, context key, source artifact, source lineage, record version, supersession status, lifecycle, conflict state.

Canonical order:
namespace type → namespace ID → context key → record version → creation sequence → global record ID

`MAX_GLOBAL_RETRIEVAL_RECORDS = 128`

No unconstrained global search or semantic ranking in the certified baseline.

## Versioning and Conflict
Records are never silently overwritten. Updates create immutable new versions with supersession linkage and change reason. Contradictory authorized context is preserved with independent provenance and `CONFLICTING` state; MERCURY does not silently choose a winner.

## Consolidation
Global summaries/consolidation must stay inside one exact namespace, preserve all source IDs/versions/provenance/conflict markers, preserve method ID/version, and remain deterministic.

`MAX_CONSOLIDATION_INPUT_RECORDS = 256`

## Promotion Limit
`MAX_PROMOTION_SOURCE_RECORDS = 128`

No silent truncation.

## Governance & Retention
Supports expiry, revocation, tombstoning, supersession, namespace closure, promotion revocation, and retention-policy enforcement. Cross-namespace fallback is forbidden.

## Critical Isolation Rule
Tenant A != Tenant B
Workspace A != Workspace B
Project A != Project B

No read, write, promotion, consolidation, or lifecycle operation may cross an unauthorized namespace boundary.

## Secret Handling
Explicitly classified credentials, passwords, API keys, authentication tokens, private-key material, and authentication secrets must not be promoted. No guessed free-form secret detection is required.

## Certified Limits
- MAX_GLOBAL_RECORDS_PER_NAMESPACE = 4096
- MAX_GLOBAL_RETRIEVAL_RECORDS = 128
- MAX_PROMOTION_SOURCE_RECORDS = 128
- MAX_CONSOLIDATION_INPUT_RECORDS = 256

## Fail-Closed Rules
Reject/fail on unauthorized namespace, cross-tenant/workspace/project access, unsupported namespace/type, missing source Phase 8 lineage, missing provenance, missing promotion or retention policy, secret-classified source, conflicting duplicate identity, invalid supersession chain, malformed version, limit violations, conflict evidence loss, forbidden user-profile/unscoped-global behavior, or malformed lifecycle.

No automatic repair. No cross-namespace fallback. No hidden profile creation.

## Forbidden Phase 9 Behavior
- unrestricted user-profile memory
- unscoped global memory
- cross-tenant memory
- model ranking/selection
- hardware placement
- scheduler decisions
- runtime execution
- semantic/vector relevance ranking
- autonomous persistence without promotion
- silent conflict resolution
- cost/latency/quality optimization

## Components
1. Global Context Contracts
2. Promotion & Admission Engine
3. Global Context Store
4. Global Retrieval Engine
5. Consolidation, Versioning & Conflict Engine
6. Governance, Retention & Isolation Engine
7. Phase 9 Certification Layer

## Implementation Tasks
1. Global Context Contract Baseline
2. Promotion & Global Admission Engine
3. Global Context Store & Namespace Isolation
4. Global Context Retrieval Engine
5. Consolidation, Versioning & Conflict Engine
6. Integration, Governance & Failure Hardening
7. Phase 9 Certification

## Exit Criteria
Phase 9 closes only when six memory types, three namespaces, five lifecycle states, explicit promotion, deterministic global IDs, namespace isolation, version/supersession lineage, conflict preservation, all four certified limits, secret rejection, revocation/expiry/tombstone behavior, no cross-tenant fallback, no implicit user profiling, no model/hardware/scheduler/runtime logic, adversarial integration, certification PASS, and full regression are all proven.
