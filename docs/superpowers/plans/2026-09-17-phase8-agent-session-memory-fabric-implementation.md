# Phase 8 Agent Session Memory Fabric Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build MERCURY X Phase 8 Agent Session Memory Fabric with deterministic, bounded, traceable, session-isolated admission, storage, retrieval, compaction, lifecycle enforcement, and certification.

**Architecture:** Phase 8 manages only short-lived session-scoped execution memory. It admits explicitly retainable artifacts, stores immutable versioned records partitioned by exact session, retrieves them through deterministic structured filters, compacts them while preserving source lineage, and enforces expiry/tombstone/session-closure lifecycle rules.

**Tech Stack:** Python 3, Pydantic immutable contracts, existing MERCURY certification framework, pytest, SHA-256 canonical digests.

**Spec:** `docs/superpowers/specs/2026-09-17-phase8-agent-session-memory-fabric-design.md`

## Global Constraints

- Certified memory types exactly: `OBSERVATION`, `INTERMEDIATE_RESULT`, `TOOL_RESULT`, `DECISION_CONTEXT`, `EXECUTION_STATE`, `COMPACTED_SUMMARY`.
- Certified scopes exactly: `TURN`, `TASK`, `SESSION`.
- Certified lifecycle states exactly: `ACTIVE`, `COMPACTED`, `EXPIRED`, `TOMBSTONED`.
- Phase result states exactly: `READY`, `NOT_APPLICABLE`, `FAIL`.
- `MAX_SESSION_MEMORY_RECORDS = 1024`.
- `MAX_RETRIEVED_RECORDS = 64`.
- `MAX_COMPACTION_INPUT_RECORDS = 128`.
- No `GLOBAL`, `USER_PROFILE`, or `CROSS_SESSION` memory scope.
- Exact session identity is mandatory for every admission, read, compaction, and lifecycle operation.
- No cross-session fallback or reuse.
- No model selection, hardware placement, scheduling, runtime execution, long-term global memory, or profile memory.
- Unknown, malformed, unsupported, incomplete, or inconsistent hard state fails closed.
- All public contracts and record versions are immutable.
- Use TDD: focused RED → minimal GREEN → focused GREEN → full suite exactly once per task.
- Do not create a worktree for this workflow.
- Do not modify certified prior phases unless a Phase 8 integration test proves a real incompatibility; if so, stop and report before broad changes.

---

## File Structure

- `src/mercury/session_memory/contracts.py`
- `src/mercury/session_memory/admission.py`
- `src/mercury/session_memory/store.py`
- `src/mercury/session_memory/retrieval.py`
- `src/mercury/session_memory/compaction.py`
- `src/mercury/session_memory/lifecycle.py`
- `src/mercury/certification/phase8.py`
- `configs/certification/phase8.json`
- `tests/test_session_memory_contracts.py`
- `tests/test_session_memory_admission_store.py`
- `tests/test_session_memory_retrieval.py`
- `tests/test_session_memory_compaction.py`
- `tests/test_session_memory_lifecycle.py`
- `tests/test_session_memory_integration_failures.py`
- `tests/test_phase8_certification.py`

---

### Task 1: Session Memory Contract Baseline

**Files:**
- Create: `src/mercury/session_memory/contracts.py`
- Test: `tests/test_session_memory_contracts.py`

**Interfaces:**
- Produces:
  - `SessionMemoryType`
  - `SessionMemoryScope`
  - `SessionMemoryLifecycle`
  - `SessionMemoryPhaseStatus`
  - `SessionMemoryRecord`
  - `SessionMemoryAdmissionRequest`
  - `SessionMemoryAdmissionResult`
  - `SessionMemoryQuery`
  - `SessionMemoryRetrievalResult`
  - `SessionMemoryCompactionRequest`
  - `SessionMemoryCompactionResult`
  - `SessionMemoryLifecycleResult`
  - `SessionMemoryLimitMetadata`
  - `canonical_session_memory_payload(...)`
  - `session_memory_record_id(...)`

**Required behavior:**
- exact vocabularies from Global Constraints;
- immutable/versioned public contracts;
- deterministic SHA-256 IDs with `sha256:` prefix;
- exact session/task/turn/source identity;
- required provenance/reason fields reject blanks;
- forbidden fields/scopes fail closed.

- [ ] Write failing tests for exact enums, immutability, deterministic IDs, blank rejection, unsupported scopes, forbidden global/profile fields, and identity stability.
- [ ] Run:
```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_session_memory_contracts.py -q
```
- [ ] Implement minimal contracts and deterministic identity helpers.
- [ ] Run focused tests until GREEN.
- [ ] Run full suite exactly once:
```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```
- [ ] Commit:
```text
feat: add Phase 8 session memory contracts
```

---

### Task 2: Memory Admission & Session Store

**Files:**
- Create: `src/mercury/session_memory/admission.py`
- Create: `src/mercury/session_memory/store.py`
- Test: `tests/test_session_memory_admission_store.py`

**Interfaces:**
- Produces:
  - `SessionMemoryAdmissionDecision`
  - `evaluate_memory_admission(...)`
  - `SessionMemoryStore`
  - `register_session_memory_record(...)`
  - deterministic store fingerprint

**Admission rules:**
- exact current-session match;
- certified type and scope only;
- explicit retainable flag required;
- explicit secret/credential classification rejects;
- bounded retention required;
- provenance required;
- source artifact identity required;
- forbidden global/profile/cross-session scope rejects.

**Store rules:**
- exact session partitioning;
- immutable versions;
- deterministic registration/order;
- semantically identical duplicates may collapse only when identity/payload match;
- conflicting duplicate identity fails closed;
- `MAX_SESSION_MEMORY_RECORDS = 1024`;
- no cross-session read/write.

- [ ] Write RED tests for valid admission, cross-session rejection, retainable=false, secret classification, missing provenance, duplicate/conflict behavior, cap enforcement, deterministic fingerprint, and immutability.
- [ ] Run:
```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_session_memory_admission_store.py -q
```
- [ ] Implement admission engine and store.
- [ ] Focused GREEN.
- [ ] Full suite once.
- [ ] Commit:
```text
feat: add Phase 8 memory admission and store
```

---

### Task 3: Session Memory Retrieval Engine

**Files:**
- Create: `src/mercury/session_memory/retrieval.py`
- Test: `tests/test_session_memory_retrieval.py`

**Interfaces:**
- Produces:
  - `retrieve_session_memory(query, store)`
  - deterministic retrieval metadata

**Filters:**
- exact session;
- task ID;
- turn range;
- memory types;
- scope;
- source artifact/lineage;
- explicit retrieval key;
- lifecycle state.

**Rules:**
- normal retrieval returns active eligible records only;
- expired/tombstoned excluded;
- exact-session authorization mandatory;
- canonical ordering:
  `session_id → task_id → turn_id → creation_sequence → record_id`;
- `MAX_RETRIEVED_RECORDS = 64`;
- caller may request smaller positive limit only;
- no global search, ranking, model-scored relevance, or cross-session lookup.

- [ ] RED tests for each filter, canonical ordering, exact-session isolation, expired/tombstoned exclusion, cap rules, deterministic permutation behavior, and immutable results.
- [ ] Run:
```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_session_memory_retrieval.py -q
```
- [ ] Implement deterministic retrieval.
- [ ] Focused GREEN.
- [ ] Full suite once.
- [ ] Commit:
```text
feat: add Phase 8 session memory retrieval
```

---

### Task 4: Memory Compaction Engine

**Files:**
- Create: `src/mercury/session_memory/compaction.py`
- Test: `tests/test_session_memory_compaction.py`

**Interfaces:**
- Produces:
  - `compact_session_memory(...)`
  - deterministic compacted `SessionMemoryRecord`

**Rules:**
- source records must belong to exact same authorized session;
- source lineage IDs/versions preserved;
- source provenance preserved;
- compaction method ID/version recorded;
- target scope explicit;
- no cross-session compaction;
- no opaque untraceable summary;
- `MAX_COMPACTION_INPUT_RECORDS = 128`;
- deterministic grouping and summary identity.

- [ ] RED tests for valid compaction, lineage preservation, provenance preservation, deterministic output, cross-session rejection, missing lineage rejection, cap enforcement, conflicting lifecycle input, and immutability.
- [ ] Run:
```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_session_memory_compaction.py -q
```
- [ ] Implement structure-preserving compaction.
- [ ] Focused GREEN.
- [ ] Full suite once.
- [ ] Commit:
```text
feat: add Phase 8 session memory compaction
```

---

### Task 5: Lifecycle, Expiry & Isolation Engine

**Files:**
- Create: `src/mercury/session_memory/lifecycle.py`
- Test: `tests/test_session_memory_lifecycle.py`

**Interfaces:**
- Produces:
  - `transition_session_memory_lifecycle(...)`
  - `expire_session_memory(...)`
  - `tombstone_session_memory(...)`
  - `close_session_memory(...)`

**Allowed transitions:**
- ACTIVE → COMPACTED
- ACTIVE → EXPIRED
- ACTIVE → TOMBSTONED
- COMPACTED → EXPIRED
- COMPACTED → TOMBSTONED

**Forbidden:**
- terminal → ACTIVE;
- mutation after expiry/tombstone;
- cross-session transition;
- unbounded retention extension;
- admission after session closure.

- [ ] RED tests for all allowed transitions, forbidden reactivation, expiry/tombstone exclusion semantics, session closure, cross-session lifecycle rejection, post-closure mutation/admission rejection, deterministic lifecycle evidence, and source immutability.
- [ ] Run:
```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_session_memory_lifecycle.py -q
```
- [ ] Implement lifecycle engine.
- [ ] Focused GREEN.
- [ ] Full suite once.
- [ ] Commit:
```text
feat: add Phase 8 memory lifecycle isolation
```

---

### Task 6: Integration & Failure Hardening

**Files:**
- Create: `tests/test_session_memory_integration_failures.py`

**Production modification:** none expected.

**End-to-end path:**
admit → store → retrieve → compact → lifecycle transition → expire/tombstone → session close.

**Cover:**
- all six memory types;
- all three scopes;
- deterministic retrieval;
- structure-preserving compaction;
- expiry;
- tombstone;
- session closure;
- READY / NOT_APPLICABLE / FAIL semantics where applicable.

**Adversarial coverage:**
- cross-session read/write;
- forbidden scope;
- unknown type/scope/lifecycle;
- secret/credential admission;
- missing provenance;
- duplicate conflicting ID;
- retrieval cap violation;
- compaction cap violation;
- compaction without lineage;
- expired/tombstoned active-read leakage;
- session-closed mutation;
- hidden GLOBAL/USER_PROFILE/CROSS_SESSION field leakage;
- long-term retention leakage;
- nondeterministic ordering;
- source mutation.

- [ ] Write integration/failure tests.
- [ ] Run:
```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_session_memory_integration_failures.py -q
```
- [ ] If a real Phase 8 defect is proven, make only the smallest exact fix and report invariant.
- [ ] Focused GREEN.
- [ ] Full suite once.
- [ ] Commit:
```text
test: harden Phase 8 session memory boundaries
```

---

### Task 7: Phase 8 Certification

**Files:**
- Create: `configs/certification/phase8.json`
- Create: `src/mercury/certification/phase8.py`
- Test: `tests/test_phase8_certification.py`

**Certification gates prove at minimum:**
1. contracts immutable/versioned;
2. exactly six memory types;
3. exactly three scopes;
4. exactly four lifecycle states;
5. `MAX_SESSION_MEMORY_RECORDS = 1024`;
6. `MAX_RETRIEVED_RECORDS = 64`;
7. `MAX_COMPACTION_INPUT_RECORDS = 128`;
8. deterministic record identity/order;
9. exact session isolation;
10. secret-classified artifacts rejected;
11. retrieval excludes expired/tombstoned records;
12. compaction preserves source lineage;
13. lifecycle transitions fail closed;
14. session closure enforcement;
15. no GLOBAL/USER_PROFILE/CROSS_SESSION behavior;
16. no long-term retention leakage;
17. no model-selection/hardware/scheduler/runtime behavior;
18. adversarial integration coverage exists.

**Evaluator behavior:**
- load config;
- reject missing/malformed/unsupported schema;
- reject duplicate gate IDs;
- reject unknown gates;
- fail on missing required artifact;
- evaluate every gate;
- never silently skip;
- deterministic aggregate;
- PASS only when all required gates PASS;
- never hardcode PASS.

- [ ] Write RED certification tests for valid config, missing/malformed/unsupported config, duplicate/unknown gate, missing artifact, vocabulary count changes, limit changes, isolation invariant break, compaction-lineage break, lifecycle break, forbidden-scope leakage.
- [ ] Run:
```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_phase8_certification.py -q
```
- [ ] Implement config/evaluator using prior certification conventions.
- [ ] Focused GREEN.
- [ ] Run:
```powershell
.\.venv\Scripts\python.exe -m mercury.certification.phase8
```
- [ ] Full suite once.
- [ ] Commit:
```text
certify: complete Phase 8 agent session memory fabric
```

---

## Self-Review

### Spec Coverage
Covered: exact type/scope/lifecycle vocabularies, admission, session isolation, deterministic store/retrieval, bounded limits, structure-preserving compaction, lifecycle transitions, session closure, secret-classified rejection, fail-closed behavior, integration hardening, and machine-readable certification.

### Placeholder Scan
No required behavior is left as TBD/TODO/implement-later.

### Type Consistency
Task 1 defines contracts used by Tasks 2–7; Task 2 owns admission/store; Task 3 retrieval; Task 4 compaction; Task 5 lifecycle/isolation; Task 6 integrated adversarial verification; Task 7 certification.

## Execution Order

`Task 1 → Task 2 → Task 3 → Task 4 → Task 5 → Task 6 → Task 7`

Do not begin a later task until the current task has focused GREEN, one full regression GREEN, a checkpoint, and a clean working tree. Do not begin Phase 9 until Phase 8 certification is PASS.
