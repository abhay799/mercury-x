# Policies & Intelligence SLOs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Build deterministic policy and SLO evaluation over the certified v1 contracts without adding scheduler ranking or placement behavior.

**Architecture:** `PolicyEvaluator` evaluates hard constraints fail-closed and exposes optimization observations without choosing a winner. `SLOEvaluator` compares measured evidence against explicit SLO targets and produces the certified `SLOResult` contract. JSON loaders validate baseline policy/SLO configuration through the existing immutable Pydantic contracts.

**Tech Stack:** Python 3.13, Pydantic v2, pytest, JSON.

**Spec:** `docs/MERCURY_X_MASTER_SPEC.md`

## Global Constraints

- Hard constraints may never be traded away for a better optimization objective.
- Policy evaluation must fail closed when a required hard-constraint fact is missing.
- Step 5 must not rank plans, select hardware/models, or schedule workloads.
- SLO results must distinguish targets from measured evidence.
- Privacy requirements are evaluated as hard requirements, not numerical optimization targets.
- Baseline config must be validated through the versioned v1 contracts.

---

### Task 1: Hard-constraint evaluation

**Files:**
- Create: `src/mercury/policy/evaluator.py`
- Test: `tests/test_policy_slo_evaluation.py`

**Interfaces:**
- Consumes: `PolicySet`, candidate facts mapping.
- Produces: `PolicyEvaluator.evaluate(...) -> PolicyEvaluation`.

- [x] Write failing equality/operator/missing-fact tests.
- [x] Run tests and verify RED due to missing evaluator.
- [x] Implement fail-closed hard-constraint evaluation.
- [x] Run focused tests and verify GREEN.

### Task 2: Optimization observations without ranking

**Files:**
- Modify: `src/mercury/policy/evaluator.py`
- Test: `tests/test_policy_slo_evaluation.py`

**Interfaces:**
- Consumes: `optimization_objectives` and candidate facts.
- Produces: objective observations and missing-objective names; no score or winner.

- [x] Test objective evidence extraction.
- [x] Implement non-ranking observation extraction.
- [x] Verify focused tests.

### Task 3: Intelligence SLO evaluation

**Files:**
- Create: `src/mercury/policy/slo_evaluator.py`
- Test: `tests/test_policy_slo_evaluation.py`

**Interfaces:**
- Consumes: `SLODefinition`, measured numerical evidence, observed privacy rule.
- Produces: immutable `SLOResult`.

- [x] Test satisfied, violated, privacy, and missing-evidence cases.
- [x] Implement explicit metric mappings and violation reasons.
- [x] Verify focused tests.

### Task 4: Validated baseline configs

**Files:**
- Create: `src/mercury/policy/config_loader.py`
- Create: `src/mercury/policy/__init__.py`
- Create: `configs/policies/default_policy.json`
- Create: `configs/slo/default_slo.json`
- Test: `tests/test_policy_slo_evaluation.py`

**Interfaces:**
- Produces: `load_policy_set(path)`, `load_slo_definition(path)`.

- [x] Test loading through certified contracts.
- [x] Add baseline config with explicit hard constraints/objectives/SLOs.
- [x] Run Step 3-5 test suites.
