# Phase 9 Global Context Memory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build MERCURY X Phase 9 Global Context Memory with explicit promotion, namespace-scoped persistence, deterministic retrieval, immutable versioning, conflict preservation, governed lifecycle, and certification.

**Architecture:** Phase 9 consumes valid Phase 8 session-memory records and promotes only explicitly authorized, persistable context into tenant/workspace/project namespaces. Records are immutable and versioned, retrieval is structured and bounded, conflicts are preserved rather than silently resolved, and governance enforces namespace isolation, retention, revocation, expiry, and tombstoning.

**Tech Stack:** Python 3, Pydantic immutable contracts, pytest, SHA-256 canonical digests, existing MERCURY certification framework.

**Spec:** `docs/superpowers/specs/2026-09-17-phase9-global-context-memory-design.md`

## Global Constraints
- Global memory types exactly: `PROJECT_CONTEXT`, `WORKSPACE_CONTEXT`, `EXECUTION_KNOWLEDGE`, `VALIDATED_FACT`, `REUSABLE_ARTIFACT_CONTEXT`, `GLOBAL_SUMMARY`.
- Namespaces exactly: `TENANT`, `WORKSPACE`, `PROJECT`.
- Lifecycle states exactly: `ACTIVE`, `SUPERSEDED`, `EXPIRED`, `REVOKED`, `TOMBSTONED`.
- Conflict states exactly: `CLEAR`, `CONFLICTING`.
- Phase statuses exactly: `READY`, `NOT_APPLICABLE`, `FAIL`.
- `MAX_GLOBAL_RECORDS_PER_NAMESPACE = 4096`.
- `MAX_GLOBAL_RETRIEVAL_RECORDS = 128`.
- `MAX_PROMOTION_SOURCE_RECORDS = 128`.
- `MAX_CONSOLIDATION_INPUT_RECORDS = 256`.
- Explicit promotion only.
- No unrestricted `USER_PROFILE` namespace.
- No cross-namespace fallback.
- Conflicting context is preserved, never silently resolved.
- No model selection, hardware placement, scheduling, runtime execution, vector/semantic ranking, or autonomous persistence.
- Unknown, malformed, unsupported, incomplete, or inconsistent hard state fails closed.
- Public contracts are immutable and versioned.
- TDD: focused RED → minimal GREEN → focused GREEN → full suite exactly once per task.
- No worktree for this workflow.

---

## File Structure
- `src/mercury/global_memory/contracts.py`
- `src/mercury/global_memory/promotion.py`
- `src/mercury/global_memory/store.py`
- `src/mercury/global_memory/retrieval.py`
- `src/mercury/global_memory/consolidation.py`
- `src/mercury/global_memory/governance.py`
- `configs/certification/phase9.json`
- `src/mercury/certification/phase9.py`
- `tests/test_global_memory_contracts.py`
- `tests/test_global_memory_promotion.py`
- `tests/test_global_memory_store.py`
- `tests/test_global_memory_retrieval.py`
- `tests/test_global_memory_consolidation.py`
- `tests/test_global_memory_integration_failures.py`
- `tests/test_phase9_certification.py`

### Task 1: Global Context Contract Baseline
**Files:** create `src/mercury/global_memory/contracts.py`; test `tests/test_global_memory_contracts.py`.

**Produces:** `GlobalMemoryType`, `GlobalMemoryNamespace`, `GlobalMemoryLifecycle`, `GlobalMemoryConflictState`, `GlobalMemoryPhaseStatus`, `GlobalContextRecord`, `GlobalPromotionRequest`, `GlobalPromotionResult`, `GlobalMemoryQuery`, `GlobalMemoryRetrievalResult`, `GlobalConsolidationRequest`, `GlobalConsolidationResult`, `GlobalGovernanceResult`, limit metadata, canonical identity helpers.

- [ ] Write failing tests for exact enums/limits, immutability, deterministic SHA-256 IDs, namespace identity, version validation, forbidden profile fields, blank IDs, and supersession fields.
- [ ] Run `./.venv/Scripts/python.exe -m pytest tests/test_global_memory_contracts.py -q` using Windows path syntax in PowerShell.
- [ ] Implement minimal immutable contracts and canonical ID helpers.
- [ ] Run focused tests until GREEN.
- [ ] Run full suite exactly once: `.\.venv\Scripts\python.exe -m pytest tests -q`.
- [ ] Commit `feat: add Phase 9 global context contracts`.

### Task 2: Promotion & Global Admission Engine
**Files:** create `src/mercury/global_memory/promotion.py`; test `tests/test_global_memory_promotion.py`.

**Produces:** `evaluate_global_promotion(...)` and deterministic promotion result.

Rules: valid Phase 8 source, explicit promotion request, exact authorized namespace, persistable flag, provenance, promotion policy ID, retention policy ID, secret rejection, source-lineage preservation, max 128 sources, no implicit importance/frequency heuristic.

- [ ] Write RED tests for valid promotion, auth mismatch, namespace mismatch, missing policies/provenance, secret classifications, 128 accepted, 129 rejected, and source immutability.
- [ ] Run `.\.venv\Scripts\python.exe -m pytest tests/test_global_memory_promotion.py -q`.
- [ ] Implement minimum engine.
- [ ] Focused GREEN, then full suite once.
- [ ] Commit `feat: add Phase 9 global promotion engine`.

### Task 3: Global Context Store & Namespace Isolation
**Files:** create `src/mercury/global_memory/store.py`; test `tests/test_global_memory_store.py`.

**Produces:** `GlobalContextStore`, `register_global_context_record(...)`, deterministic store fingerprint, exact-namespace access helpers.

Rules: strict namespace partition, immutable versions, deterministic registration, identical duplicate collapse only when canonical content matches, conflicting duplicate reject, 4096 cap per exact namespace, no cross-namespace access.

- [ ] RED tests for registration, isolation, duplicates/conflicts, cap, deterministic fingerprint, permutations, and immutability.
- [ ] Run `.\.venv\Scripts\python.exe -m pytest tests/test_global_memory_store.py -q`.
- [ ] Implement store.
- [ ] Focused GREEN, then full suite once.
- [ ] Commit `feat: add Phase 9 global context store`.

### Task 4: Global Context Retrieval Engine
**Files:** create `src/mercury/global_memory/retrieval.py`; test `tests/test_global_memory_retrieval.py`.

**Produces:** `retrieve_global_context(query, store)`.

Filters: namespace type/ID, memory type, context key, source artifact, source lineage, version, lifecycle, supersession status, conflict state.

Canonical order: namespace type → namespace ID → context key → record version → creation sequence → record ID. Max 128. No semantic/vector/LLM ranking.

- [ ] RED tests for every filter, exact namespace isolation, lifecycle behavior, canonical order, 128 cap, invalid limits, permutations, and absence of ranking fields.
- [ ] Run `.\.venv\Scripts\python.exe -m pytest tests/test_global_memory_retrieval.py -q`.
- [ ] Implement deterministic retrieval.
- [ ] Focused GREEN, then full suite once.
- [ ] Commit `feat: add Phase 9 global context retrieval`.

### Task 5: Consolidation, Versioning & Conflict Engine
**Files:** create `src/mercury/global_memory/consolidation.py`; test `tests/test_global_memory_consolidation.py`.

**Produces:** `create_global_record_version(...)`, `consolidate_global_context(...)`.

Rules: no overwrite; immutable new version; deterministic version increment; required supersession linkage/change reason; preserve provenance. Contradictory context remains independently traceable and marked `CONFLICTING`. Consolidation stays inside one exact namespace, max 256, preserves source IDs/versions/provenance/conflict markers/method ID-version.

- [ ] RED tests for versioning, supersession, invalid chain, conflict preservation, deterministic consolidation, cross-namespace reject, 256/257 limits, and immutability.
- [ ] Run `.\.venv\Scripts\python.exe -m pytest tests/test_global_memory_consolidation.py -q`.
- [ ] Implement minimum engine.
- [ ] Focused GREEN, then full suite once.
- [ ] Commit `feat: add Phase 9 versioning and conflict consolidation`.

### Task 6: Integration, Governance & Failure Hardening
**Files:** create `src/mercury/global_memory/governance.py`; create `tests/test_global_memory_integration_failures.py`.

**Produces:** expiry/revocation/tombstone operations and namespace closure/governance helpers.

End-to-end path: Phase 8 source → promotion → global store → retrieval → version/consolidation → conflict → governance lifecycle.

Adversarial coverage: cross-tenant/workspace/project access, secret promotion, missing policy/provenance, malformed supersession, conflict evidence loss, cap violations, revoked/expired/tombstoned active-read leakage, namespace closure, no profile/unscoped-global behavior, determinism, source immutability.

- [ ] Write RED integration/governance tests.
- [ ] Run `.\.venv\Scripts\python.exe -m pytest tests/test_global_memory_integration_failures.py -q`.
- [ ] Implement governance and only minimum proven fixes.
- [ ] Focused GREEN, then full suite once.
- [ ] Commit `test: harden Phase 9 global context boundaries`.

### Task 7: Phase 9 Certification
**Files:** create `configs/certification/phase9.json`, `src/mercury/certification/phase9.py`, `tests/test_phase9_certification.py`.

Certification proves: exact six types, three namespaces, five lifecycle states, two conflict states, exact statuses, 4096/128/128/256 limits, deterministic IDs, explicit promotion, namespace authorization/isolation, secret rejection, immutable versioning/supersession, conflict preservation, deterministic non-ranking retrieval, governance lifecycle, no USER_PROFILE/unscoped-global behavior, no semantic/vector ranking, no model/hardware/scheduler/runtime behavior, and adversarial integration coverage.

Evaluator rejects missing/malformed/unsupported config, duplicate/unknown gates, missing artifacts, skipped gates, and returns PASS only when all required gates PASS.

- [ ] Write RED certification tests.
- [ ] Run `.\.venv\Scripts\python.exe -m pytest tests/test_phase9_certification.py -q`.
- [ ] Implement config/evaluator using Phase 0–8 conventions.
- [ ] Focused GREEN.
- [ ] Run `.\.venv\Scripts\python.exe -m mercury.certification.phase9`.
- [ ] Run full suite once.
- [ ] Commit `certify: complete Phase 9 global context memory`.

## Self-Review
Spec coverage: promotion, namespace isolation, deterministic identities, store, retrieval, versioning, supersession, conflicts, consolidation, governance, limits, secret rejection, forbidden boundaries, and certification are each assigned to a task.

Placeholder scan: no TBD/TODO/implement-later requirements remain.

Type consistency: Task 1 defines shared contracts; Task 2 promotion; Task 3 store; Task 4 retrieval; Task 5 versioning/consolidation/conflict; Task 6 governance/integration; Task 7 certification.

## Execution Order
`Task 1 → Task 2 → Task 3 → Task 4 → Task 5 → Task 6 → Task 7`

Do not begin a later task until the current task has focused GREEN, one full regression GREEN, a checkpoint, and a clean working tree. Do not begin Phase 10 until Phase 9 certification is PASS.
