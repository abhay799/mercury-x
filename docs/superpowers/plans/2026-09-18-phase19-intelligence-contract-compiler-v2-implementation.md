# MERCURY X Phase 19 Intelligence Contract Compiler v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Compile application-facing SLAs into immutable, machine-enforceable Intelligence SLO contracts with typed metrics, policy hierarchy, temporal semantics, conflict detection, error budgets, provenance, and no silent weakening.

**Architecture:** Phase 19 is implemented as a compiler pipeline: parse/normalize → metric resolution → constraint typing → policy inheritance → conflict detection → temporal/error-budget compilation → composite objective construction → validation → immutable versioned Intelligence SLO.

**Tech Stack:** Python, Pydantic, deterministic canonical identity/fingerprints, pytest, generic requirement interfaces consumed by Phase 17/18.

**Spec:** `docs/superpowers/specs/2026-09-18-phase19-sla-intelligence-contract-compiler-v2-design.md`

## Global Constraints

- Constraint types exactly HARD/SOFT/UNKNOWN.
- UNKNOWN never means permissive.
- `degradation_allowed = false` by default.
- Bare untyped quality numbers are invalid.
- Hard constraints cannot be weakened through weighting.
- Privacy/safety/authorization hard rules have no implicit error budget.
- Contracts are immutable and versioned.
- No placement, scheduling, execution, model selection, or negotiation acceptance.

---

### Task 1: Compiler Contracts and Generic Requirement Interface

**Files:**
- Create: `src/mercury/intelligence_slo/__init__.py`
- Create: `src/mercury/intelligence_slo/contracts.py`
- Test: `tests/test_intelligence_slo_contracts.py`

- [ ] RED tests for exact constraint/outcome enums, immutable version fields, degradation default false, deterministic IDs, and invalid bare quality thresholds.
- [ ] Implement `ApplicationSLA`, `ConstraintKind`, `IntelligenceRequirement`, `IntelligenceSLO`, `CompilationStatus`, version/provenance contracts.
- [ ] Confirm GREEN.

### Task 2: Metric Registry

**Files:**
- Create: `src/mercury/intelligence_slo/metrics.py`
- Test: `tests/test_intelligence_slo_metrics.py`

- [ ] RED tests for metric definition semantics, evaluator identity, threshold direction, aggregation rule, workload-class scope, duplicate metric IDs, undefined metric failure.
- [ ] Implement deterministic registry.
- [ ] Confirm GREEN.

### Task 3: SLA Parser / Normalizer

**Files:**
- Create: `src/mercury/intelligence_slo/normalize.py`
- Test: `tests/test_intelligence_slo_normalize.py`

- [ ] RED tests for canonical normalization, unit normalization where explicitly supported, duplicate constraint rejection, ambiguity preservation, input immutability.
- [ ] Implement normalization.
- [ ] Confirm GREEN.

### Task 4: Hard/Soft/Unknown Constraint Classifier

**Files:**
- Create: `src/mercury/intelligence_slo/classify.py`
- Test: `tests/test_intelligence_slo_classify.py`

- [ ] RED tests for explicit hard/soft/unknown, absent classification -> UNKNOWN, safety/privacy/authorization preservation, and no implicit softening.
- [ ] Implement classifier.
- [ ] Confirm GREEN.

### Task 5: Policy Hierarchy Engine

**Files:**
- Create: `src/mercury/intelligence_slo/policy.py`
- Test: `tests/test_intelligence_slo_policy.py`

- [ ] RED tests for organization→tenant→application→workload-class→workload inheritance, conflicting parent/child hard constraints, explicit override authority, deterministic merge order.
- [ ] Implement policy inheritance and conflict reporting.
- [ ] Confirm GREEN.

### Task 6: Temporal / Tail Semantics

**Files:**
- Create: `src/mercury/intelligence_slo/temporal.py`
- Test: `tests/test_intelligence_slo_temporal.py`

- [ ] RED tests for percentile latency, rolling window, burst constraint, availability window, logical-generation deterministic test mode, invalid percentile/window.
- [ ] Implement temporal target contracts/evaluation.
- [ ] Confirm GREEN.

### Task 7: Error Budget Engine

**Files:**
- Create: `src/mercury/intelligence_slo/error_budget.py`
- Test: `tests/test_intelligence_slo_error_budget.py`

- [ ] RED tests for explicit allowed violation budgets, zero implicit safety/privacy/authorization budget, deterministic consumption, budget exhaustion, and temporal scope.
- [ ] Implement error-budget model.
- [ ] Confirm GREEN.

### Task 8: Composite Objective Compiler

**Files:**
- Create: `src/mercury/intelligence_slo/objectives.py`
- Test: `tests/test_intelligence_slo_objectives.py`

- [ ] RED tests for AND/OR structures, allowed weighted soft objectives, hard-constraint non-weighting, deterministic canonical expression, invalid circular objective graph.
- [ ] Implement composite objective compiler.
- [ ] Confirm GREEN.

### Task 9: Conflict / Satisfiability Analyzer

**Files:**
- Create: `src/mercury/intelligence_slo/conflicts.py`
- Test: `tests/test_intelligence_slo_conflicts.py`

- [ ] RED tests for impossible quality/latency pair, contradictory residency/privacy, incompatible retry/verification, undefined metric, overlapping policy conflict, AMBIGUOUS and UNSATISFIABLE distinction.
- [ ] Implement deterministic analyzer.
- [ ] Confirm GREEN.

### Task 10: Template Expansion

**Files:**
- Create: `src/mercury/intelligence_slo/templates.py`
- Test: `tests/test_intelligence_slo_templates.py`

- [ ] RED tests for explicit workload-class template expansion, provenance retention, versioned template identity, and template conflict detection.
- [ ] Implement template system.
- [ ] Confirm GREEN.

### Task 11: Compiler Assembly

**Files:**
- Create: `src/mercury/intelligence_slo/compiler.py`
- Test: `tests/test_intelligence_slo_compiler.py`

- [ ] RED end-to-end tests for parse→metric resolution→classification→policy→conflict→temporal/error-budget→objective→canonical SLO.
- [ ] Implement compiler pipeline.
- [ ] Confirm GREEN.

### Task 12: Immutable Version Lifecycle

**Files:**
- Create: `src/mercury/intelligence_slo/lifecycle.py`
- Test: `tests/test_intelligence_slo_lifecycle.py`

- [ ] RED tests for new version on change, previous-version reference, changed-constraint provenance, unchanged input identity stability, no in-place mutation.
- [ ] Implement lifecycle.
- [ ] Confirm GREEN.

### Task 13: Phase 17/18 Generic Interface Integration

**Files:**
- Create: `src/mercury/intelligence_slo/integration.py`
- Test: `tests/test_intelligence_slo_integration.py`

- [ ] RED tests proving Phase 19 output satisfies the generic interface consumed by Phase 17/18 without those phases importing Phase 19 internals.
- [ ] Implement adapter/protocol compatibility.
- [ ] Confirm GREEN.

### Task 14: Adversarial Hardening

**Files:**
- Create: `tests/test_intelligence_slo_integration_failures.py`

- [ ] Cover ambiguous metrics, malicious template override, policy contradiction, hidden degradation flag, zero-evidence metric, invalid provenance, impossible temporal objective, unknown-as-permissive attack.
- [ ] Fix one invariant at a time.

### Task 15: Executable Certification

**Files:**
- Create: `configs/certification/phase19.json`
- Create: `src/mercury/certification/phase19.py`
- Create: `src/mercury/certification/phase19_checks.py`
- Test: `tests/test_phase19_certification.py`

- [ ] Certification must execute real compiler behaviors for registry, typing, hierarchy, temporal semantics, error budgets, versioning, conflict detection, provenance, degradation=false, ambiguity fail-closed.
- [ ] No unconditional placeholder gates.

### Task 16: Final Verification

- [ ] Run focused Phase 19.
- [ ] Run Phase 17/18 compatibility.
- [ ] Run certification.
- [ ] Run full regression.
- [ ] Run `git diff --check`.
