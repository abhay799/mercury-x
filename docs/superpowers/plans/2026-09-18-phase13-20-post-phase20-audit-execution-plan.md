# MERCURY X Phase 13–20 Post-Phase-20 Audit Execution Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans with systematic-debugging and verification-before-completion. This is a hardening gate, not a feature phase.

**Goal:** Audit and harden Phases 13–20 as one integrated compute-intelligence block before Phase 21 starts.

**Architecture:** Codex inspects design promises, actual implementation, tests, certification, boundary integration, state machines, evidence/calibration semantics, concurrency, and quality-preservation invariants. Findings are fixed with regression tests and then every phase is re-certified.

**Tech Stack:** Existing MERCURY Python/Pydantic/pytest stack, Git, Windows-safe pytest temp/cache.

**Spec:** `docs/superpowers/specs/2026-09-18-phase13-20-post-phase20-codex-audit-contract.md`

## Global Constraints

- No Phase 21 work until this audit closes.
- Do not reset or discard existing certified work.
- Do not hide or rename compromises instead of fixing them.
- Every discovered defect gets a regression test before the fix.
- No placeholder/unconditional certification gates.
- No automatic or implicit quality reduction anywhere in Phase 13–20.
- Preserve CPU-first baseline while keeping GPU/cloud-capable architecture intact.

---

### Task 1: Baseline Inventory

- [ ] Record HEAD, clean/dirty status, latest Phase 13–20 design/plan paths, current test counts, current certification outputs.
- [ ] Map each design requirement to implementation files/tests/certification gates.
- [ ] Produce a findings matrix: implemented / partial / missing / overclaimed.

### Task 2: Phase 13–16 Deep Audit

- [ ] Audit Hardware Personality evidence semantics, identity, trust lifecycle, capability/affinity derivation.
- [ ] Audit topology directionality, path semantics, locality, evidence, stale/invalid profile integration.
- [ ] Audit placement eligibility, scoring, uncertainty/calibration, topology and hardware integration, pluggable backend boundary.
- [ ] Audit speculative execution branch lifecycle, bounded fan-out, verification-before-commit, cancellation/discard, provenance, retry semantics, concurrency.
- [ ] Add RED tests for every concrete finding.
- [ ] Fix findings one at a time.

### Task 3: Phase 17–20 Deep Audit

- [ ] Audit budget difficulty/cost/quality models, Pareto frontier, allocation, escalation/stop, counterfactuals, lifecycle.
- [ ] Audit scheduler fairness, starvation, preemption, backfill, gang scheduling, speculation accounting, forecasting, fragmentation.
- [ ] Audit SLO compiler metrics, hierarchy, temporal semantics, error budgets, conflict resolution, versioning, provenance.
- [ ] Audit negotiator feasibility, propagation, Pareto offers, rounds, leases, approval, atomicity, concurrency, revocation, history.
- [ ] Add RED tests for every concrete finding.
- [ ] Fix findings one at a time.

### Task 4: Cross-Phase Boundary Audit

- [ ] Verify typed boundaries across 12→13→14→15→16→17→18→19→20.
- [ ] Detect magic strings, duck typing, circular dependencies, hidden mutation, duplicated authority, and semantic reinterpretation.
- [ ] Fix only at the correct ownership boundary.

### Task 5: Certification Integrity Audit

- [ ] Enumerate every Phase 13–20 certification gate.
- [ ] Prove each gate executes a real invariant and can fail under a deliberately broken fixture.
- [ ] Remove placeholder structural passes and overly broad shared checks that do not prove the named invariant.
- [ ] Validate duplicate/unknown/missing manifest gates fail closed.

### Task 6: Adversarial / Concurrency / Failure Audit

- [ ] Add missing malformed-input, stale-generation, conflicting-evidence, replay, race, double-commit, state-transition, expiry, revocation, and mutation tests.
- [ ] Verify no UNKNOWN is interpreted as success where hard proof is required.

### Task 7: Calibration / Learned Backend Honesty

- [ ] Confirm all deterministic baselines are labelled honestly.
- [ ] Confirm no empirical probability/quality/performance claim exists without calibration evidence.
- [ ] Confirm learned/pluggable outputs pass through deterministic hard constraints.

### Task 8: Quality-Preservation Audit

- [ ] Search all Phase 13–20 code paths for quality-floor rewriting or lower-quality fallback.
- [ ] Prove via tests that overload/scarcity causes defer/counteroffer/reject/unknown rather than silent quality reduction.
- [ ] Verify Phase 20 cannot propose lower quality under the locked policy.

### Task 9: Re-Certification

- [ ] Run focused suites for Phase 13, 14, 15, 16, 17, 18, 19, 20.
- [ ] Run each phase certification executable.
- [ ] Run cross-phase compatibility tests.
- [ ] Run full repository regression with Windows-safe temp/cache.
- [ ] Run `git diff --check`.
- [ ] Require explicit zero-known-in-scope-compromise report or list unresolved blockers; do not start Phase 21 if blockers remain.
