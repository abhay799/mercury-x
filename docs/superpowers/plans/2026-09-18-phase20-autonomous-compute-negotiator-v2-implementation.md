# MERCURY X Phase 20 Autonomous Compute Negotiator v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a full-strength, versioned, multi-round compute negotiation control plane that preserves quality and hard constraints, produces Pareto offers, requires explicit approval, supports leases/concurrency/atomic commit/revocation, and never auto-degrades.

**Architecture:** Phase 20 composes typed Phase 15/16/17/18/19 evidence into a feasibility solver and negotiation state machine. Offers are immutable, bounded by explicit leases and resource-snapshot generations, and only become agreements after explicit approval plus atomic revalidation.

**Tech Stack:** Python, Pydantic, deterministic IDs/fingerprints, pytest, existing Phase 15–19 interfaces.

**Spec:** `docs/superpowers/specs/2026-09-18-phase20-autonomous-compute-negotiator-v2-design.md`

## Global Constraints

- Outcomes exactly ACCEPT/COUNTEROFFER/REJECT/UNKNOWN.
- No AUTO_DEGRADE.
- Quality floor cannot be lowered by MERCURY.
- Hard safety/privacy/authorization/residency/verification constraints are non-negotiable.
- Counteroffers require explicit approval artifact.
- Silence is never approval.
- Stale/expired offers cannot be accepted.
- Agreement commit is atomic against resource snapshot generation.
- No execution, provisioning, migration, or in-place SLO mutation.
- Phase 20 is a hard stop before the Phase 13–20 Codex audit.

---

### Task 1: Negotiation Contracts

**Files:**
- Create: `src/mercury/compute_negotiator/__init__.py`
- Create: `src/mercury/compute_negotiator/contracts.py`
- Test: `tests/test_compute_negotiator_contracts.py`

- [ ] RED tests for outcome enum, lifecycle enum, request/offer/approval/agreement contracts, deterministic IDs, no lower-quality offer, lease generation validation.
- [ ] Implement typed contracts and canonical identity.
- [ ] Confirm GREEN.

### Task 2: Feasibility Solver

**Files:**
- Create: `src/mercury/compute_negotiator/feasibility.py`
- Test: `tests/test_compute_negotiator_feasibility.py`

- [ ] RED tests for feasible SLO, insufficient quality, insufficient verification, privacy/residency conflict, no eligible placements, unknown evidence, resource shortage with deferrable path.
- [ ] Implement feasibility states and evidence-rich reason codes.
- [ ] Confirm GREEN.

### Task 3: Constraint Propagation Engine

**Files:**
- Create: `src/mercury/compute_negotiator/constraints.py`
- Test: `tests/test_compute_negotiator_constraints.py`

- [ ] RED tests propagating quality, latency, verification, privacy, residency, safety, authorization, compute, reasoning, speculation, scheduling constraints; contradictions explicit.
- [ ] Implement deterministic propagation.
- [ ] Confirm GREEN.

### Task 4: Pareto Offer Generator

**Files:**
- Create: `src/mercury/compute_negotiator/offers.py`
- Test: `tests/test_compute_negotiator_offers.py`

- [ ] RED tests for non-dominated offers varying latency/resource envelope/placement/speculation/wait while holding quality floor fixed, duplicate/dominated offer removal, deterministic ordering.
- [ ] Implement offer frontier.
- [ ] Confirm GREEN.

### Task 5: Multi-Round Negotiation State Machine

**Files:**
- Create: `src/mercury/compute_negotiator/state.py`
- Test: `tests/test_compute_negotiator_state.py`

- [ ] RED tests for REQUESTED→EVALUATING→OFFERED/COUNTEROFFERED→ACCEPTED/REJECTED/EXPIRED/REVOKED and illegal transitions.
- [ ] Implement immutable rounds referencing previous round and snapshot generation.
- [ ] Confirm GREEN.

### Task 6: Offer Lease and Expiry

**Files:**
- Create: `src/mercury/compute_negotiator/lease.py`
- Test: `tests/test_compute_negotiator_lease.py`

- [ ] RED tests for logical-generation validity, expiry, stale resource snapshot, invalid negative/zero lease.
- [ ] Implement deterministic lease checks.
- [ ] Confirm GREEN.

### Task 7: Explicit Approval Artifact

**Files:**
- Create: `src/mercury/compute_negotiator/approval.py`
- Test: `tests/test_compute_negotiator_approval.py`

- [ ] RED tests for exact offer ID, approver authority reference, accepted changed constraints, generation, fingerprint, mismatch rejection, silence/no artifact rejection.
- [ ] Implement approval validation.
- [ ] Confirm GREEN.

### Task 8: Atomic Agreement Commit

**Files:**
- Create: `src/mercury/compute_negotiator/commit.py`
- Test: `tests/test_compute_negotiator_commit.py`

- [ ] RED tests for valid commit, stale offer, resource-generation mismatch, authorization mismatch, hard-constraint drift, double commit.
- [ ] Implement compare-and-validate style atomic control-plane commit model.
- [ ] Confirm GREEN.

### Task 9: Concurrency Control

**Files:**
- Create: `src/mercury/compute_negotiator/concurrency.py`
- Test: `tests/test_compute_negotiator_concurrency.py`

- [ ] RED tests for two negotiations targeting exclusive envelope, generation conflict, deterministic conflict winner policy only where explicitly allowed, otherwise fail closed.
- [ ] Implement deterministic concurrency guard.
- [ ] Confirm GREEN.

### Task 10: Revocation and Re-Negotiation

**Files:**
- Create: `src/mercury/compute_negotiator/revocation.py`
- Test: `tests/test_compute_negotiator_revocation.py`

- [ ] RED tests for resource envelope disappearance before execution, authorization revocation, no silent substitute, new negotiation required.
- [ ] Implement revocation transitions.
- [ ] Confirm GREEN.

### Task 11: Negotiation History / Provenance

**Files:**
- Create: `src/mercury/compute_negotiator/history.py`
- Test: `tests/test_compute_negotiator_history.py`

- [ ] RED tests for append-only rounds/offers/approvals/rejections/expiry/revocation, deterministic history fingerprint, no deletion/rewrite.
- [ ] Implement immutable history model.
- [ ] Confirm GREEN.

### Task 12: Phase 15–19 Integration

**Files:**
- Create: `src/mercury/compute_negotiator/integration.py`
- Test: `tests/test_compute_negotiator_integration.py`

- [ ] RED tests for typed consumption of placement predictions, speculation bounds, reasoning budgets, scheduling state, Intelligence SLO, and resource snapshot without mutating any source.
- [ ] Implement typed adapters.
- [ ] Confirm GREEN.

### Task 13: Negotiation Orchestrator

**Files:**
- Create: `src/mercury/compute_negotiator/negotiator.py`
- Test: `tests/test_compute_negotiator_negotiator.py`

- [ ] RED tests for ACCEPT, COUNTEROFFER, REJECT, UNKNOWN; no lower-quality counteroffer; explicit approval requirement; stale offer rejection; deterministic result.
- [ ] Implement orchestration.
- [ ] Confirm GREEN.

### Task 14: Adversarial Hardening

**Files:**
- Create: `tests/test_compute_negotiator_integration_failures.py`

- [ ] Cover quality downgrade attack, forged approval, replayed approval, stale offer acceptance, resource race, changed SLO during negotiation, hidden provider substitution, invalid authorization, double commit, unknown-as-accept, history tampering.
- [ ] Fix one invariant at a time.

### Task 15: Executable Certification

**Files:**
- Create: `configs/certification/phase20.json`
- Create: `src/mercury/certification/phase20.py`
- Create: `src/mercury/certification/phase20_checks.py`
- Test: `tests/test_phase20_certification.py`

- [ ] Certification must prove no quality-reduction path, feasibility, constraint propagation, Pareto offers, multi-round versioning, stale-offer rejection, explicit approval, atomic commit, concurrency safety, revocation, history completeness, UNKNOWN fail closed, and no execution side effects.
- [ ] No placeholder PASS gates.

### Task 16: Final Verification and Hard Stop

- [ ] Run focused Phase 20.
- [ ] Run Phase 15–19 compatibility.
- [ ] Run Phase 20 certification.
- [ ] Run full regression.
- [ ] Run `git diff --check`.
- [ ] Do not begin Phase 21.
- [ ] Execute the separate Phase 13–20 Codex audit/hardening contract.
