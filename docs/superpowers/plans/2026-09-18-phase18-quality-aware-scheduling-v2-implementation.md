# MERCURY X Phase 18 Quality-Aware Scheduling v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a full-strength quality-aware scheduling intelligence layer with admission control, fairness, starvation protection, preemption intent, backfilling, gang scheduling, speculation accounting, forecasting boundaries, and fragmentation awareness.

**Architecture:** Phase 18 consumes certified readiness, compatibility, placement, speculation, reasoning-budget, and generic intelligence-requirement inputs. It emits deterministic scheduling decisions and intents but performs no runtime side effects.

**Tech Stack:** Python, Pydantic contracts, deterministic canonical IDs/fingerprints, pytest, existing MERCURY Phase 12–17 contracts.

**Spec:** `docs/superpowers/specs/2026-09-18-phase18-quality-aware-scheduling-v2-design.md`

## Global Constraints

- No silent quality degradation.
- Hard compatibility/topology/authorization/SLO requirements fail closed.
- Deterministic logical generations for fairness/starvation tests.
- No runtime execution, migration, provisioning, or SLO rewriting.
- Distributed-ready interfaces; certification may use local deterministic simulation.
- CPU-first final certification.

---

### Task 1: Scheduling Contracts

**Files:**
- Create: `src/mercury/quality_scheduler/__init__.py`
- Create: `src/mercury/quality_scheduler/contracts.py`
- Test: `tests/test_quality_scheduler_contracts.py`

**Interfaces:**
- Produces exact `AdmissionState` = ADMIT/DEFER/REJECT/UNKNOWN and `PriorityClass` = CRITICAL/HIGH/NORMAL/LOW plus `SchedulingRequest`, `SchedulingFeatures`, `SchedulingDecision`, `PreemptionIntent`, `GangRequirement`.

- [ ] Write RED tests for exact enums, deterministic IDs, queue metadata validation, duplicate candidate rejection, and no negative logical generations.
- [ ] Implement contracts and canonical identity.
- [ ] Confirm focused GREEN.

### Task 2: Admission Controller

**Files:**
- Create: `src/mercury/quality_scheduler/admission.py`
- Test: `tests/test_quality_scheduler_admission.py`

- [ ] RED tests for incompatible hardware, invalid topology, ineligible Phase 15 candidate, unsatisfied hard intelligence requirement, insufficient evidence -> UNKNOWN, impossible request -> REJECT, temporary capacity pressure -> DEFER.
- [ ] Implement fail-closed admission.
- [ ] Confirm GREEN.

### Task 3: Multi-Objective Priority Engine

**Files:**
- Create: `src/mercury/quality_scheduler/priority.py`
- Test: `tests/test_quality_scheduler_priority.py`

- [ ] RED tests covering deadline pressure, quality-risk pressure, verification, uncertainty, reasoning-budget pressure, placement confidence, logical age, fairness weight, resource pressure, topology locality, fragmentation cost, deterministic tie-break.
- [ ] Implement explicit feature contribution/reason codes; no hidden learned weights.
- [ ] Confirm GREEN.

### Task 4: Fairness and Starvation Guard

**Files:**
- Create: `src/mercury/quality_scheduler/fairness.py`
- Test: `tests/test_quality_scheduler_fairness.py`

- [ ] RED tests for logical aging, starvation ceiling, tenant fairness, expensive long-job starvation prevention, and deterministic fairness adjustments.
- [ ] Implement fairness guard.
- [ ] Confirm GREEN.

### Task 5: Preemption Policy

**Files:**
- Create: `src/mercury/quality_scheduler/preemption.py`
- Test: `tests/test_quality_scheduler_preemption.py`

- [ ] RED tests proving preemption requires recoverability/checkpoint semantics, does not violate victim hard SLO, emits intent only, and is deterministic.
- [ ] Implement preemption-intent evaluation.
- [ ] Confirm GREEN.

### Task 6: Backfilling

**Files:**
- Create: `src/mercury/quality_scheduler/backfill.py`
- Test: `tests/test_quality_scheduler_backfill.py`

- [ ] RED tests for safe idle-window filling, protected-work non-delay, unknown-duration fail closed, and deterministic selection.
- [ ] Implement backfill planner.
- [ ] Confirm GREEN.

### Task 7: Gang / Co-Scheduling

**Files:**
- Create: `src/mercury/quality_scheduler/gang.py`
- Test: `tests/test_quality_scheduler_gang.py`

- [ ] RED tests for all-or-nothing certified resource set, partial-resource rejection/defer, topology constraints, and deterministic group IDs.
- [ ] Implement gang feasibility/intents.
- [ ] Confirm GREEN.

### Task 8: Speculative Work Accounting

**Files:**
- Create: `src/mercury/quality_scheduler/speculation_accounting.py`
- Test: `tests/test_quality_scheduler_speculation_accounting.py`

- [ ] RED tests ensuring Phase 16 branches consume visible resource budget, cannot exceed Phase 17/16 bounds, and cannot invisibly starve protected workloads.
- [ ] Implement accounting.
- [ ] Confirm GREEN.

### Task 9: Fragmentation Awareness

**Files:**
- Create: `src/mercury/quality_scheduler/fragmentation.py`
- Test: `tests/test_quality_scheduler_fragmentation.py`

- [ ] RED tests for fragmented resource sets, gang fragmentation, locality fragmentation, deterministic penalty/reason codes, and no invented future availability.
- [ ] Implement fragmentation model.
- [ ] Confirm GREEN.

### Task 10: Queue Pressure Forecasting Backend Boundary

**Files:**
- Create: `src/mercury/quality_scheduler/forecast.py`
- Test: `tests/test_quality_scheduler_forecast.py`

- [ ] RED tests for deterministic baseline, pluggable empirical/learned backend protocol, explicit calibration state, uncertainty, and hard-constraint override prevention.
- [ ] Implement deterministic baseline + protocol.
- [ ] Confirm GREEN.

### Task 11: Scheduler Assembly

**Files:**
- Create: `src/mercury/quality_scheduler/scheduler.py`
- Test: `tests/test_quality_scheduler_scheduler.py`

- [ ] RED tests for combined admission + priority + fairness + fragmentation + speculation accounting, deterministic queue order, and immutable input state.
- [ ] Implement assembly/orchestration only.
- [ ] Confirm GREEN.

### Task 12: Adversarial Hardening

**Files:**
- Create: `tests/test_quality_scheduler_integration_failures.py`

- [ ] Add tests for starvation attack, priority inversion, impossible gang request, speculative resource flood, conflicting deadline/quality constraints, unknown topology, stale placement, invalid reasoning budget, and no runtime side effects.
- [ ] Fix one invariant at a time.

### Task 13: Executable Certification

**Files:**
- Create: `configs/certification/phase18.json`
- Create: `src/mercury/certification/phase18.py`
- Create: `src/mercury/certification/phase18_checks.py`
- Test: `tests/test_phase18_certification.py`

- [ ] Certification must prove deterministic ordering, hard-constraint protection, fairness/starvation behavior, preemption safety, backfill safety, gang correctness, speculation accounting, fragmentation behavior, forecast honesty, no quality degradation, no runtime side effects.
- [ ] No unconditional placeholder PASS.

### Task 14: Final Verification

- [ ] Run focused Phase 18.
- [ ] Run Phase 12–17 compatibility.
- [ ] Run Phase 18 certification.
- [ ] Run full regression.
- [ ] Run `git diff --check`.
- [ ] Report known gaps honestly.
