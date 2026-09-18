# MERCURY X Benchmarks and Evidence

## Purpose

This report states what the repository can currently prove, how to reproduce that evidence, and what remains unmeasured. It separates functional correctness from performance, simulation, and demonstration evidence. No control-plane artifact is presented as a deployed accelerator or datacenter result.

The maintained machine-readable inventory is [EVIDENCE_MANIFEST.json](EVIDENCE_MANIFEST.json). A local run produces `artifacts/evidence/mercury_evidence.json`; that snapshot is ignored by Git because it contains environment-specific results.

## Evidence taxonomy

| Classification | Precise meaning | Permitted interpretation |
|---|---|---|
| `MEASURED` | Observed by an executed command in a named local environment. | Only the recorded property, command, environment, and sample. |
| `SYNTHETIC` | Produced from constructed fixtures or generated workloads rather than production traffic. | The code handles the tested logical case. |
| `SIMULATED` | Produced by a software model of a system or event rather than the physical system represented. | The modeled behavior follows the tested simulation rules. |
| `STATIC_DEMO` | Rendered from maintained fixtures without live telemetry or control authority. | The UI presents deterministic demonstration state. |
| `UNCALIBRATED` | Produced by a model without empirical calibration evidence for predictive accuracy. | Advisory exploration only; no accuracy claim. |
| `NOT_MEASURED` | No responsible empirical measurement exists in maintained repository evidence. | No quantitative claim may be inferred. |

Classifications may be combined. For example, an executed test is `MEASURED` as a local command result while its inputs remain `SYNTHETIC`.

## Current evidence summary

| Evidence area | Classification | What it supports | What it does not support |
|---|---|---|---|
| Phase 0-30 artifact coverage | `SYNTHETIC` | Control-plane implementations, contracts, and internal gates exist across the intended scope. | Deployment readiness or external certification. |
| Python regression | `MEASURED` + `SYNTHETIC` | Tested behavior and repository-wide compatibility in the recorded local environment. | Production throughput, latency, scale, or model quality. |
| Certification checks | `MEASURED` + `SYNTHETIC` | Internal architecture and completeness gates execute and reject known invalid states. | Regulatory, security, standards, or third-party certification. |
| Control Center | `MEASURED` + `STATIC_DEMO` + `SYNTHETIC` | Static rendering, provenance labels, view coverage, and smoke behavior. | Live telemetry or operational control. |
| Demo scenarios | `MEASURED` + `STATIC_DEMO` + `SYNTHETIC` + `SIMULATED` | Deterministic lifecycle, safety, rollback, and cross-view projections. | Observed production incidents or physical migration. |
| Datacenter twin | `SIMULATED` + `UNCALIBRATED` | Advisory modeled behavior within tested rules. | Predictive accuracy for a real facility. |
| Infrastructure performance | `NOT_MEASURED` | No performance claim. | Any GPU, cloud, network, federation, cost, power, or production scheduling result. |

The repository previously recorded **1506 passing tests** during final Phase 26-30 validation. That value is **HISTORICAL**, not the current result. The generated snapshot is authoritative for a new run.

### Fresh local evidence snapshot

The following results were generated at `2026-09-18T02:35:48Z` from commit `c8139934ae543673dbe212ebc585da237217c724` with the productization changes present as an uncommitted working-tree diff. Environment: Windows 11, AMD64, Python 3.13.9, Node.js 24.18.0, npm 11.16.0. Durations are one observed command wall-time sample and are reproducibility metadata, not control-plane performance benchmarks.

| Check | Result | Observed duration | Classification and scope |
|---|---:|---:|---|
| Full Python regression | 1506 passed | 6.935 s | `MEASURED` command result over `SYNTHETIC` tests; local compatibility only |
| Certification-focused tests | 256 passed | 5.472 s | `MEASURED` command result over `SYNTHETIC` gates; internal certification only |
| Phase 30 certification CLI | PASS | 0.427 s | `MEASURED` + `SYNTHETIC`; repository safe-research-mode gate |
| Control Center validation | PASS: 11 modules, 15 views, 314 provenance-bearing artifacts, static HTTP smoke | 1.821 s | `MEASURED` + `STATIC_DEMO` + `SYNTHETIC` |
| Scenario validation | PASS: six deterministic scenarios | 0.728 s | `MEASURED` + `STATIC_DEMO` + `SYNTHETIC` + `SIMULATED` |

The machine-readable source for these values is the generated `artifacts/evidence/mercury_evidence.json`. Because that file is intentionally Git-ignored, rerun the evidence runner to reproduce or replace the snapshot.

## Functional correctness evidence

The strongest current evidence is contract and decision correctness over deterministic, synthetic inputs:

- immutable or versioned artifacts with identity and provenance checks;
- exact compatibility and capability validation across models, precision, morphing, topology, and placement;
- fail-closed behavior for missing, stale, contradictory, unauthorized, or malformed state;
- quality/SLO preservation and explicit negotiation outcomes;
- migration state-machine, authoritative-executor, rollback, and recovery invariants;
- self-healing detection, bounded response, verification, escalation, and safe-state behavior;
- adversarial scheduler challenges and advisory-only counterfactual evaluation;
- controlled policy promotion with evidence and human authorization;
- federation, privacy, residency, and cross-scope isolation safeguards;
- digital-twin advisory boundaries and supervisory human-control behavior.

This is functional correctness evidence for the tested software paths. It is not performance evidence.

## Certification evidence

The repository contains a manifest and evaluator for every numbered phase from 0 through 30. Certification-focused tests exercise required-gate coverage, malformed configuration, deterministic aggregation, boundary leakage, and fail-closed outcomes. Phase 30 also exposes an executable CLI check.

These certifications are internal repository architecture/completeness gates. They are not external audits and must not be represented as regulatory, security, industry, or third-party certification.

## Safety invariant evidence

Tests and certification gates cover the normative invariants summarized in [SAFETY_INVARIANTS.md](../architecture/SAFETY_INVARIANTS.md), including:

- no silent relaxation of quality, safety, verification, authorization, privacy, residency, or agreed SLO constraints;
- generation-aware stale-state rejection;
- deterministic provenance and tamper-evident identities;
- advisory separation for simulation and counterfactual output;
- controlled policy promotion;
- exactly one authoritative executor during migration cutover;
- explicit reject, defer, counteroffer, rollback, or escalation outcomes.

Passing these checks demonstrates enforcement in tested code paths only.

## Scenario and demonstration evidence

The Control Center contains six deterministic scenario definitions: normal orchestration, quality/SLO conflict, live migration, self-healing, adversarial counterfactual analysis, and federated privacy/residency. Validation checks their lifecycle transitions, terminal states, reset behavior, provenance, audit trail, safety boundaries, and cross-view projection.

The scenarios are fixture-backed. Their records are `STATIC_DEMO`, `SYNTHETIC`, and, where they model infrastructure events, `SIMULATED`. They never become live evidence merely because they are rendered in an operational-style interface.

## Performance evidence

The evidence runner measures command wall time for local validation and records the environment. Those durations describe only the named validation command on that machine at that time. They are reproducibility metadata, not a throughput or latency benchmark for MERCURY X control decisions.

No standalone control-plane microbenchmark is maintained in this baseline. Existing paths combine validation, fixture construction, file access, and interpreter overhead; extracting attractive timing figures would create weak or misleading performance claims. Meaningful performance work requires a separately reviewed workload, sampling method, environment record, and interpretation boundary.

## Simulated evidence

Counterfactual, migration, federation, recovery, and datacenter scenarios may represent behavior that would occur in physical infrastructure. Their local outputs remain simulated logical decisions. Simulation can establish deterministic rule handling and safety boundaries; it cannot establish physical transfer speed, downtime, scaling, or savings.

## Uncalibrated components

The Phase 28 datacenter twin and any predictive or advisory model without an attached empirical calibration artifact are `UNCALIBRATED`. The repository can test schema, provenance, deterministic behavior, and advisory boundaries, but it does not establish real-world prediction accuracy.

## Not-measured capabilities

The following are explicitly `NOT_MEASURED`:

- GPU inference throughput;
- multi-GPU scaling;
- cloud distributed throughput;
- real network transfer performance;
- physical live-migration downtime;
- physical GPU-memory migration;
- real datacenter power savings;
- production scheduler improvement;
- real model-quality improvement;
- calibrated digital-twin prediction accuracy;
- production federation latency;
- real-world cost savings.

No estimate or extrapolation is supplied for these capabilities.

## Reproduction instructions

From the repository root after following [RUNNING.md](../RUNNING.md):

```powershell
.\.venv\Scripts\python.exe scripts\evidence\validate_evidence.py
.\.venv\Scripts\python.exe scripts\evidence\run_evidence.py
```

The second command runs certification-focused checks, the Phase 30 CLI, both Control Center validators, and one Windows-safe full Python regression. It writes:

```text
artifacts/evidence/mercury_evidence.json
```

For a faster structural and UI/certification check that makes no current full-regression claim:

```powershell
.\.venv\Scripts\python.exe scripts\evidence\run_evidence.py --skip-python-tests
```

Inspect the snapshot's `git`, `environment`, `checks`, `summary`, classifications, and claim boundary together. Do not copy a result without its context.

## Interpretation guidance

1. Treat the evidence classification as part of every claim.
2. A `PASS` applies only to the recorded command and checked behavior.
3. Test count is not a measure of system performance or product maturity.
4. Internal certification is not third-party certification.
5. Static demonstrations are not live operations.
6. Simulation is not measurement of the represented physical system.
7. Command duration is validation metadata unless a reviewed benchmark methodology says otherwise.
8. A missing measurement remains `NOT_MEASURED`; it is not zero and must not be estimated.

## Limitations

The baseline requires no GPU, cloud account, distributed cluster, or paid service. Consequently it cannot support claims about those environments. Local results may vary with interpreter, operating system, filesystem, and machine load. The runner deliberately records only coarse environment details and does not collect hostnames, credentials, endpoints, or unnecessary hardware identifiers.

See [LIMITATIONS.md](../LIMITATIONS.md) for the broader product boundary.
