# MERCURY X Testing & Certification Framework

## Phase gate
IMPLEMENT → UNIT TEST → INTEGRATION TEST → FAILURE TEST → BENCHMARK → ARTIFACT VALIDATION → DOCUMENTATION → CERTIFICATION → GIT CHECKPOINT

A phase is not certified merely because code exists or unit tests pass.

## Required test families
- Contract validation tests
- Component unit tests
- Integration tests
- Failure-injection tests
- Benchmark validation
- Security/privacy validation
- Regression suite

## Fail-closed certification
Any required checklist item that is missing, NOT_RUN, or FAIL prevents certification.

## Evidence
Certification records should reference exact test outputs, benchmark artifacts, configuration versions, and documentation versions. Simulated evidence must remain marked SIMULATED; measured evidence must remain marked MEASURED.

## Preflight
The machine-readable checklist in `configs/certification/preflight.json` defines the pre-development gate before Phase 0 implementation.

The checklist covers every Master Spec pre-development gate: architecture,
scope, schemas, interfaces, policies, registries, artifact manifest,
environment, dependency lock, repository structure, CPU strategy, remote GPU
strategy, benchmarks, SLOs, telemetry, failure model, security, testing,
certification, cloud budget controls, and documentation.

The required artifact manifest is `configs/artifacts/manifest.json`. It stores
registered artifact metadata and validates required artifact paths, readiness,
and SHA-256 checksums before its gate can be marked PASS.

## Passing Certification Record

A machine-readable passing record is written to
`configs/certification/preflight-record.json` only after every required
checklist item is PASS with non-empty evidence. The record format rejects
blank evidence, failed statuses, and missing evidence. Loading or creating a
record requires its named checklist and rejects unknown or incomplete status
coverage; it is not a substitute for the commands and artifact validation
cited as its evidence.

## Current Preflight Remediation Evidence

The current record contains all 21 mandatory gates as PASS. The associated
full regression command completed with `61 passed` using the project-local
Python interpreter.
