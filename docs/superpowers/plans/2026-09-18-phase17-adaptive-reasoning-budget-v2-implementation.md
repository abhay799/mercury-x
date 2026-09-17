# MERCURY X Phase 17 Adaptive Reasoning Budget v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a full-strength adaptive reasoning-budget control plane that minimizes compute only inside a protected intelligence-quality envelope.

**Architecture:** Phase 17 is decomposed into typed contracts, difficulty/cost/quality models, Pareto frontier construction, allocation, escalation/stop control, counterfactual budget simulation, pluggable policy backends, immutable generations, and executable certification. Learned or empirical policies remain advisory behind deterministic hard-constraint validation.

**Tech Stack:** Python, Pydantic contracts, deterministic canonical JSON/SHA-256 identity, pytest, existing MERCURY Phase 12–16 contracts.

**Spec:** `docs/superpowers/specs/2026-09-18-phase17-adaptive-reasoning-budget-v2-design.md`

## Global Constraints

- Do not lower hard quality, confidence, verification, privacy, safety, authorization, or residency constraints.
- No model/precision/provider/region/placement/scheduling/runtime selection.
- Baseline backend may be deterministic but must expose empirical/learned backend interfaces.
- Baseline calibration must be explicitly `UNCALIBRATED`.
- Equivalent inputs must produce deterministic IDs, frontiers, allocations, reason codes, and fingerprints.
- No hidden user profiling.
- CPU-first certification.
- All tests use Windows-safe pytest temp/cache on final verification.

---

### Task 1: Reasoning Budget Contracts and Identity

**Files:**
- Create: `src/mercury/reasoning_budget/__init__.py`
- Create: `src/mercury/reasoning_budget/contracts.py`
- Test: `tests/test_reasoning_budget_contracts.py`

**Interfaces:**
- Produces: `WorkloadDifficulty`, `ReasoningBudgetDecisionState`, `BudgetCalibrationState`, `ReasoningBudgetRequest`, `ReasoningBudgetCandidate`, `ReasoningBudget`, `ReasoningBudgetDecision`, `make_reasoning_budget_id()`.

- [ ] **Step 1: Write failing contract tests** for exact enum values, invalid negative ceilings, duplicate provenance IDs, deterministic IDs, immutable tuple ordering, and required quality metric definition.
- [ ] **Step 2: Run** `python -m pytest tests/test_reasoning_budget_contracts.py -q` and confirm RED due to missing module/types.
- [ ] **Step 3: Implement the contracts** using existing `ContractModel`, nonnegative/positive bounds, canonical tuple validators, and canonical JSON + SHA-256 helpers.
- [ ] **Step 4: Run the focused tests** and confirm GREEN.
- [ ] **Step 5: Review API names** against the spec before moving on.

### Task 2: Workload Difficulty Estimator

**Files:**
- Create: `src/mercury/reasoning_budget/difficulty.py`
- Test: `tests/test_reasoning_budget_difficulty.py`

**Interfaces:**
- Consumes: `ReasoningBudgetRequest`.
- Produces: `DifficultyAssessment` and `estimate_difficulty(request, evidence) -> DifficultyAssessment`.

- [ ] **Step 1: Add RED tests** for LOW/MEDIUM/HIGH/EXTREME/UNKNOWN, conflicting evidence, missing evidence -> UNKNOWN, permutation invariance, and no hidden user fields.
- [ ] **Step 2: Run tests and confirm RED.**
- [ ] **Step 3: Implement deterministic evidence-backed estimation** with reason codes and provenance. No evidence means UNKNOWN.
- [ ] **Step 4: Run tests and confirm GREEN.**

### Task 3: Reasoning Cost Model

**Files:**
- Create: `src/mercury/reasoning_budget/cost.py`
- Test: `tests/test_reasoning_budget_cost.py`

**Interfaces:**
- Produces: `ReasoningCostEstimate`, `ReasoningCostBackend`, `DeterministicReasoningCostBackend`.

- [ ] **Step 1: Add RED tests** for step/token/verification/speculation cost accounting, nonnegative results, deterministic output, and uncalibrated metadata.
- [ ] **Step 2: Confirm RED.**
- [ ] **Step 3: Implement a deterministic baseline** driven only by explicit input features and typed envelopes.
- [ ] **Step 4: Confirm GREEN.**

### Task 4: Marginal Quality Gain Model

**Files:**
- Create: `src/mercury/reasoning_budget/quality_gain.py`
- Test: `tests/test_reasoning_budget_quality_gain.py`

**Interfaces:**
- Produces: `QualityGainEstimate`, `QualityGainBackend`, `DeterministicQualityGainBackend`.

- [ ] **Step 1: Add RED tests** for monotonic nonnegative gain ranges, evidence lineage, valid-domain checks, UNKNOWN outside domain, and `UNCALIBRATED` baseline.
- [ ] **Step 2: Confirm RED.**
- [ ] **Step 3: Implement a conservative deterministic baseline** that never claims empirical probabilities or measured quality gains.
- [ ] **Step 4: Confirm GREEN.**

### Task 5: Pareto Budget Frontier Engine

**Files:**
- Create: `src/mercury/reasoning_budget/frontier.py`
- Test: `tests/test_reasoning_budget_frontier.py`

**Interfaces:**
- Produces: `dominates(a, b) -> bool`, `build_budget_frontier(candidates) -> tuple[ReasoningBudgetCandidate, ...]`.

- [ ] **Step 1: Add RED tests** for dominated option removal, equal candidates, quality preservation, deterministic ordering, permutation invariance, and UNKNOWN estimate handling.
- [ ] **Step 2: Confirm RED.**
- [ ] **Step 3: Implement non-dominated frontier construction** across quality floor, latency, compute, verification depth, speculation width, and uncertainty.
- [ ] **Step 4: Confirm GREEN.**

### Task 6: Budget Allocator

**Files:**
- Create: `src/mercury/reasoning_budget/allocation.py`
- Test: `tests/test_reasoning_budget_allocation.py`

**Interfaces:**
- Produces: `BudgetAllocation`, `allocate_budget(request, chosen_candidate) -> BudgetAllocation`.

- [ ] **Step 1: Add RED tests** for allocation among primary reasoning, verification, speculation, retries/escalations, final aggregation, and total-envelope conservation.
- [ ] **Step 2: Confirm RED.**
- [ ] **Step 3: Implement deterministic allocation** with no allocation above request ceilings and no allocation below hard verification minimums.
- [ ] **Step 4: Confirm GREEN.**

### Task 7: Escalation and Stop Controllers

**Files:**
- Create: `src/mercury/reasoning_budget/control.py`
- Test: `tests/test_reasoning_budget_control.py`

**Interfaces:**
- Produces: `evaluate_escalation(...)`, `evaluate_stop(...)`.

- [ ] **Step 1: Add RED tests** for confidence shortfall, verification failure, uncertainty overflow, quality shortfall, branch disagreement, hard ceiling reached, no escalation path, and successful stop.
- [ ] **Step 2: Confirm RED.**
- [ ] **Step 3: Implement deterministic controllers** with explicit reason codes.
- [ ] **Step 4: Confirm GREEN.**

### Task 8: Counterfactual Budget Simulator

**Files:**
- Create: `src/mercury/reasoning_budget/counterfactual.py`
- Test: `tests/test_reasoning_budget_counterfactual.py`

**Interfaces:**
- Produces: `CounterfactualBudgetScenario`, `simulate_budget_alternatives(...)`.

- [ ] **Step 1: Add RED tests** for step increase, speculation-width increase, verification-depth increase, latency expansion, deterministic ordering, and advisory-only metadata.
- [ ] **Step 2: Confirm RED.**
- [ ] **Step 3: Implement side-effect-free simulation** using backend interfaces.
- [ ] **Step 4: Confirm GREEN.**

### Task 9: Immutable Budget Generation / Refresh

**Files:**
- Create: `src/mercury/reasoning_budget/lifecycle.py`
- Test: `tests/test_reasoning_budget_lifecycle.py`

**Interfaces:**
- Produces: `build_reasoning_budget(...)`, `refresh_reasoning_budget(...)`.

- [ ] **Step 1: Add RED tests** for generation increment, old-generation immutability, fingerprint changes only when canonical state changes, and stale-evidence refresh.
- [ ] **Step 2: Confirm RED.**
- [ ] **Step 3: Implement lifecycle functions.**
- [ ] **Step 4: Confirm GREEN.**

### Task 10: Phase 15/16 Integration

**Files:**
- Create: `src/mercury/reasoning_budget/integration.py`
- Test: `tests/test_reasoning_budget_integration.py`

**Interfaces:**
- Consumes typed Phase 15 prediction confidence and Phase 16 branch bounds.
- Produces normalized explicit evidence used by the Phase 17 engine.

- [ ] **Step 1: Add RED tests** proving no duck typing, no Phase 15 score mutation, no widening Phase 16 branch limits, and UNKNOWN when evidence is insufficient.
- [ ] **Step 2: Confirm RED.**
- [ ] **Step 3: Implement typed adapters only.**
- [ ] **Step 4: Confirm GREEN.**

### Task 11: Adversarial Hardening

**Files:**
- Create: `tests/test_reasoning_budget_integration_failures.py`

- [ ] **Step 1: Add adversarial tests** for conflicting evidence, impossible quality/latency/compute envelope, duplicate candidates, invalid calibration claims, negative/overflow budgets, hidden quality reduction, mutated input detection, and boundary leakage.
- [ ] **Step 2: Run and fix failures one invariant at a time.**

### Task 12: Executable Certification

**Files:**
- Create: `configs/certification/phase17.json`
- Create: `src/mercury/certification/phase17.py`
- Create: `src/mercury/certification/phase17_checks.py`
- Test: `tests/test_phase17_certification.py`

- [ ] **Step 1: Write RED certification tests** proving malformed manifests, duplicate/unknown/missing gates, and broken invariants fail certification.
- [ ] **Step 2: Implement executable checks** for all spec-critical invariants; no unconditional placeholder PASS.
- [ ] **Step 3: Run focused certification GREEN.**

### Task 13: Final Verification

- [ ] **Step 1:** Run all Phase 17 tests with Windows-safe temp/cache.
- [ ] **Step 2:** Run `python -m mercury.certification.phase17`.
- [ ] **Step 3:** Run Phase 15/16 compatibility.
- [ ] **Step 4:** Run full regression.
- [ ] **Step 5:** Run `git diff --check`.
- [ ] **Step 6:** Report remaining known limitations explicitly; do not call Phase 17 closed if research-grade items promised by the spec are missing.
