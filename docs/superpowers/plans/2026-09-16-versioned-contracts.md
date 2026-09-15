# MERCURY X Versioned Contracts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add strict, versioned MERCURY X boundary contracts without changing the two already-passing workload and execution-graph contracts.

**Architecture:** Keep contracts as immutable Pydantic v2 models under `src/mercury/contracts`. Contracts describe data crossing component boundaries only; registries, scheduling algorithms, runtime behavior, and optimization logic remain in later pre-development steps.

**Tech Stack:** Python 3.13.9, Pydantic v2, pytest 9.1.1.

**Spec:** `docs/MERCURY_X_MASTER_SPEC.md`

## Global Constraints

- Preserve existing `src/mercury/contracts/workload.py` and `src/mercury/graph/models.py`.
- Every boundary contract carries an explicit `schema_version`.
- Breaking schema changes require a new version rather than silent mutation.
- Strictly reject unknown fields at contract boundaries.
- Keep simulated and measured hardware evidence distinct.
- Keep logical graph contracts separate from physical execution-plan contracts.
- No registry lookup, scheduler scoring, runtime execution, or cloud integration belongs in Step 3.

---

### Task 1: Contract Test Harness

**Files:**
- Create: `tests/test_versioned_contracts.py`

**Interfaces:**
- Consumes: Pydantic validation and the agreed schema identifiers.
- Produces: behavior checks for all new Step 3 contracts.

- [x] Write failing tests for missing versioned contracts.
- [x] Run tests and verify they fail because contracts are absent.

### Task 2: Workload Boundary Contracts

**Files:**
- Create: `src/mercury/contracts/base.py`
- Create: `src/mercury/contracts/workload_request.py`
- Create: `src/mercury/contracts/workload_profile.py`

**Interfaces:**
- Consumes: external request fields from the master specification.
- Produces: `WorkloadRequest`, `WorkloadProfile`.

- [x] Implement strict immutable base contract.
- [x] Implement `mercury.workload.request/v1`.
- [x] Implement `mercury.workload.profile/v1`.

### Task 3: Registry Profile Contracts

**Files:**
- Create: `src/mercury/contracts/model_profile.py`
- Create: `src/mercury/contracts/hardware_profile.py`

**Interfaces:**
- Produces: `ModelProfile`, `HardwareProfile` for later registry implementation.

- [x] Implement model capability schema.
- [x] Implement hardware capability schema with measured/simulated evidence distinction.
- [x] Validate available memory cannot exceed total memory.

### Task 4: Physical Planning and Scheduling Contracts

**Files:**
- Create: `src/mercury/contracts/execution_plan.py`
- Create: `src/mercury/contracts/schedule_decision.py`

**Interfaces:**
- Produces: `ExecutionPlan`, `ScheduleDecision`, `CandidateAlternative`.

- [x] Keep physical assignments separate from logical DAG definitions.
- [x] Record predicted metrics and policy version.
- [x] Record selected plan rationale and rejection reasons for alternatives.

### Task 5: Runtime, Telemetry, SLO, and Policy Contracts

**Files:**
- Create: `src/mercury/contracts/runtime_event.py`
- Create: `src/mercury/contracts/telemetry.py`
- Create: `src/mercury/contracts/slo.py`
- Create: `src/mercury/contracts/policy.py`

**Interfaces:**
- Produces: `RuntimeEvent`, `TelemetryRecord`, `SLODefinition`, `SLOResult`, `PolicySet`, `OptimizationObjective`.

- [x] Add runtime event contract.
- [x] Add measured telemetry contract with timestamp ordering validation.
- [x] Separate SLO targets from SLO evidence/results.
- [x] Separate hard constraints from optimization objectives.

### Task 6: Verification

- [x] Run Step 3 contract tests.
- [x] Run the complete user repository suite after extraction. Evidence:
  `.venv\\Scripts\\python.exe -m pytest tests -v` reported 61 passed during
  preflight remediation.
- [x] Certify Step 3 only after the existing two tests and all new contract tests pass together. Evidence:
  `configs/certification/preflight-record.json` records the fully passing
  preflight gate, including `mercury.execution.graph/v1` coverage.
