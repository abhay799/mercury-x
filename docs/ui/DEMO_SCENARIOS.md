# MERCURY X End-to-End Demo Scenarios

## Purpose

The scenario system turns the Control Center into a reproducible demonstration of MERCURY X control-plane decisions. It shows why a workload advances, defers, rejects, counteroffers, rolls back, or escalates while preserving provenance and hard safety invariants.

Scenario data is not production telemetry. It does not represent real datacenter operation, physical GPU/VM migration, calibrated infrastructure prediction, or autonomous production scheduling.

## Architecture

```text
Control Center views
        ↓
Scenario Controller
        ↓
Scenario Control Center Provider
        ↓
Deterministic scenario catalog + current step
        ↓
Generic projection over the existing demo snapshot
        ↓
Mission Control / Workloads / Compute / SLO / Migration /
Scheduler / Federation / Evidence views
```

The implementation is centralized under `ui/control-center/src/scenarios/`:

- `contracts.js` validates schemas, identities, statuses, provenance, contiguous sequences, events, and terminal states.
- `definitions.js` contains the six immutable scenarios and their deterministic steps.
- `controller.js` owns selection and start/reset/previous/next transitions.
- `scenario-provider.js` projects the current scenario over the existing Control Center snapshot.

Scenario logic is not embedded in view components. Existing views consume the projected provider snapshot through the same data boundary used by the original static demonstration.

## Scenario Contract

Each scenario preserves:

- schema and scenario ID;
- name and description;
- source type, evidence state, and calibration state;
- workload and affected-resource identities;
- ordered deterministic steps;
- logical time rather than wall-clock timing;
- current and expected terminal states;
- safety decisions;
- event/audit records;
- optional rollback or verification-failure branches;
- immutable provenance references.

Each step records its decision, evidence, authority, safety result, verification result, affected resources, route, and provenance.

## Scenario 1 — Normal Workload Orchestration

An incoming text-reasoning workload proceeds through gateway normalization, workload classification, logical graph construction, exact model capability, BF16 precision compatibility, context resolution, topology evaluation, placement prediction, reasoning budget, Intelligence SLO, compute agreement, execution authorization, verification, and successful completion.

Demonstrated invariant: identity, quality floor, authorization, and verification remain explicit from request to completion.

Expected terminal state: `ACCEPT`.

## Scenario 2 — Quality / SLO Conflict

A workload requests quality floor `0.92` and 31 logical resource units. The demonstration resource envelope exposes only 18 units. A hypothetical cheaper path would violate the quality floor, so MERCURY rejects that degradation, preserves verification depth, requests compatible resources, and emits an explicit counteroffer.

The numeric values are synthetic control-plane fixtures, not empirical model-quality or hardware benchmarks.

Expected terminal state: `COUNTEROFFER`.

## Scenario 3 — Live Workload Migration

A simulated degradation trigger starts the Phase 21 control lifecycle: eligibility, destination qualification, execution-state checkpoint, state/context-reference transfer, provisional restore, equivalence verification, atomic cutover, and source retirement.

Node A remains authoritative until verified cutover. Node B becomes the sole authority atomically. Verification or cutover failure follows the inspectable rollback path to a safe source state.

This is control-plane migration simulation/state orchestration. It is not OS, VM, container, device-memory, or physical GPU-memory migration.

Expected terminal state: `ACCEPT` with exactly one authoritative executor.

## Scenario 4 — Self-Healing Failure Recovery

A synthetic node degradation produces evidence, bounded recovery candidates, an authorized reversible recovery, and post-action verification. Unsafe candidates that weaken quality, authorization, privacy, or SLO constraints are rejected.

The main path resumes after verification. The modeled failure branch is `VERIFICATION_FAILED → ROLLBACK_SAFE_STATE → ESCALATE`.

Expected terminal state: `ACCEPT` on the verified main path.

## Scenario 5 — Adversarial Scheduling and Counterfactual Analysis

An initially plausible scheduling decision is challenged for starvation pressure and stale topology evidence. The stale decision is rejected. Counterfactual alternatives are evaluated as `SIMULATED`, `ADVISORY`, and `UNCALIBRATED`; they cannot authorize execution.

The safer recommendation is to refresh evidence and defer affected work.

Expected terminal state: `DEFER`.

## Scenario 6 — Federated Privacy / Residency

Three exact execution domains are evaluated against a confidential-data privacy envelope requiring IN residency and minimum-necessary access. The EU domain is rejected for residency mismatch, and a research domain is rejected for insufficient production authority. A compliant IN domain is selected and redacted evidence is recorded.

Capability does not imply authorization. Insufficient evidence or authority fails closed.

Expected terminal state: `ACCEPT` for the compliant candidate.

## Scenario Player

The Scenario Player provides:

- a six-scenario selector;
- description and provenance;
- start, reset, previous, and next controls;
- current logical time and lifecycle stage;
- ordered lifecycle visualization;
- decision/evidence/authority details;
- affected resources;
- safety invariant panel;
- expected terminal outcome;
- rollback and alternate-failure paths;
- deterministic audit trail.

Autoplay is intentionally omitted. Manual deterministic transitions keep evidence and cause/effect inspectable.

## Cross-View Synchronization

The scenario provider is authoritative. It projects the selected step into existing domain views rather than creating unrelated duplicate state:

- Mission Control shows the active scenario and current decision stage.
- Workloads receives the scenario workload and current state.
- Compute Fabric shows affected resources.
- SLO & Reasoning exposes the quality/resource conflict.
- Migration & Recovery follows migration or healing steps.
- Scheduler Intelligence shows advisory challenge state.
- Federation & Privacy shows candidate decisions.
- Evidence & Audit receives deterministic scenario events.

## Provenance Model

Allowed scenario source types are:

- `SYNTHETIC`
- `SIMULATED`
- `STATIC DEMO`
- `UNKNOWN`

The scenario contracts reject `LIVE`. Simulated predictions declare calibration state, and current counterfactual/migration/healing scenarios remain `UNCALIBRATED` where applicable.

## Determinism and Reproducibility

- Scenario definitions are immutable.
- Logical timestamps use fixed `T+NNN` values.
- Step sequences are contiguous and fixed.
- Selection and reset return the same initial state.
- No random values, wall-clock decisions, network calls, or machine state influence playback.
- Every scenario has a reachable explicit terminal step.

## Safety Behavior

- No automatic quality degradation exists.
- Unknown or stale evidence cannot authorize execution.
- Hard privacy, residency, authorization, verification, and SLO constraints fail closed.
- Counterfactual results remain advisory.
- Migration maintains exactly one authoritative executor.
- Healing cannot resume before verification.
- Policy and scenario recommendations cannot autonomously promote or execute.

## Audit Trail

Every completed scenario step generates a deterministic audit record containing:

- event ID;
- scenario and workload IDs;
- logical timestamp;
- decision and evidence identity;
- authority;
- provenance;
- safety result;
- verification result;
- outcome.

The Control Center Evidence & Audit view displays the current event alongside the base demonstration records.

## Run the Demos

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m http.server 4173 --directory ui/control-center
```

Open `http://127.0.0.1:4173/#/scenarios`.

## Validate

```powershell
Set-Location ui/control-center
npm.cmd run check:scenarios
npm.cmd run check
```

The focused scenario validator proves catalog completeness, deterministic reset, transition and terminal-state correctness, provenance, audit integrity, quality protection, migration authority, simulation boundaries, federation filtering, and cross-view projection. The general validator checks all JavaScript modules, all linked views, provider provenance, and static HTTP delivery.

## Runtime Boundary and Limitations

- Playback changes an in-browser demonstration snapshot only.
- No Python runtime package is imported or modified.
- No workload, scheduler, migration, healing, federation, or policy action is executed.
- Resource values and logical times are demonstration fixtures.
- The system is not connected to real telemetry or authentication.
- A future authenticated API provider can replace the demo/scenario provider while retaining the existing view contract.

