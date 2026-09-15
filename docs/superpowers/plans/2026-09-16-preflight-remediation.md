# MERCURY X Pre-Flight Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repair all verified preflight discrepancies without beginning Phase 0.

**Architecture:** Preserve the legacy logical graph model and introduce only a
strict versioned graph boundary contract. Certification gains a validated
artifact manifest, complete Master Spec gate coverage, and an evidence-backed
record. Environment and Git changes remain local, reproducible, and free of
new runtime, GPU, cloud, or remote dependencies.

**Tech Stack:** Python 3.13.9, Pydantic v2, pytest 9.1.1, JSON, local Git.

**Spec:** `docs/superpowers/specs/2026-09-16-preflight-remediation-design.md`

## Global Constraints

- Do not begin Phase 0, scheduler, runtime, worker, or GPU/cloud execution.
- Preserve existing certified contracts; breaking changes require a new version.
- Keep `ExecutionGraph` logical and `ExecutionPlan` physical.
- Never represent simulated data as measured evidence.
- Paid cloud remains disabled by default; no cloud/GPU dependencies are added.
- Never commit secrets, credentials, `.venv`, caches, or generated/private artifacts.
- Every production behavior change follows RED → GREEN with focused tests.
- Create the certification record only after all mandatory gates pass.

---

### Task 1: Versioned logical execution-graph contract

**Files:**
- Create: `src/mercury/contracts/execution_graph.py`
- Modify: `tests/test_versioned_contracts.py`
- Modify: `tests/test_execution_graph.py`

**Interfaces:**
- Produces: `ExecutionGraph`, `GraphNode`, and `GraphEdge`, all strict
  `ContractModel` instances.
- `ExecutionGraph.schema_version` is exactly `mercury.execution.graph/v1`.
- The legacy `AIExecutionGraph` remains unmodified.

- [x] Write failing tests for a valid logical v1 DAG, unknown/physical-field
  rejection, invalid references, cycles, immutability, and legacy graph
  compatibility.
- [x] Run the focused tests and confirm failure because the v1 contract is absent.
- [x] Implement the smallest strict logical contract with DAG validation.
- [x] Re-run the focused tests and confirm they pass.

### Task 2: Artifact manifest and integrity validation

**Files:**
- Create: `src/mercury/certification/artifact_manifest.py`
- Create: `configs/artifacts/manifest.json`
- Modify: `tests/test_certification_framework.py`

**Interfaces:**
- Produces: versioned `ArtifactManifest`/`ArtifactRecord`, loader, and
  integrity validator rooted at the repository directory.
- Each record has identifier, name, relative path, creator, consumers,
  schema version, required flag, checksum, version, and readiness status.

- [x] Write failing tests for valid manifest loading, duplicate IDs, missing
  files, unsafe paths, and checksum mismatch.
- [x] Run them and confirm failure because the manifest implementation is absent.
- [x] Implement models, loader, SHA-256 validation, and the canonical manifest.
- [x] Re-run focused tests and confirm they pass.

### Task 3: Complete checklist coverage and certification record

**Files:**
- Modify: `configs/certification/preflight.json`
- Modify: `src/mercury/certification/models.py`
- Modify: `src/mercury/certification/evaluator.py`
- Modify: `tests/test_certification_framework.py`

**Interfaces:**
- The checklist covers all Master Spec pre-development gate items, including
  scope, dependency lock, and repository structure.
- A certification record stores evaluated statuses and evidence only when all
  required statuses are PASS.

- [x] Write failing tests for required added checklist items and rejection of
  a record with a non-PASS required item.
- [x] Run focused tests and confirm failure for missing coverage/record rules.
- [x] Implement the minimal record validation and checklist additions.
- [x] Re-run focused tests and confirm they pass.

### Task 4: Local environment reproducibility

**Files:**
- Modify: `environment.md`
- Modify: `pytest.ini` or add only required project import metadata/configuration
- Modify: relevant tests

**Interfaces:**
- The documented validation uses `.venv\\Scripts\\python.exe`.
- A direct project-local interpreter import of `mercury` succeeds by the
  documented setup, independent of pytest-only path injection.

- [x] Write a failing subprocess test for direct `import mercury` with no
  `PYTHONPATH` injection.
- [x] Run it and confirm the present import failure.
- [x] Implement only the smallest local packaging/import configuration justified
  by the inspected environment; do not change application dependencies.
- [x] Re-run the focused test and the documented validation command.

### Task 5: Local Git baseline and ignore verification

**Files:**
- Modify: `.gitignore` only if inspection shows an unprotected local artifact.
- Create: `.git/` by local `git init` only if Git remains absent.

- [x] Reconfirm Git is absent with `git rev-parse --git-dir`.
- [x] Initialize a local repository with no remote and no commit/push.
- [x] Verify `git check-ignore` protects `.venv`, `.env`, secrets, caches,
  generated/private artifacts, and certification scratch state.

### Task 6: Evidence, traceability, and certification

**Files:**
- Modify: `docs/superpowers/plans/2026-09-16-versioned-contracts.md`
- Modify: `docs/superpowers/plans/2026-09-16-benchmark-workloads.md`
- Modify: `docs/superpowers/plans/2026-09-16-testing-certification-framework.md`
- Create: `configs/certification/preflight-record.json` only if all gates pass.
- Update: `configs/artifacts/manifest.json` checksums after final documentation changes.

- [x] Run focused certification/manifest/graph tests.
- [x] Run `.venv\\Scripts\\python.exe -m pytest tests -v`.
- [x] Evaluate every checklist item with fresh evidence.
- [x] Create the passing preflight record only after the evaluator reports no
  missing required items.
- [x] Update stale plan statuses using the actual commands/results and verify
  manifest integrity again.
- [x] Bind passing records to their named checklist and require complete,
  nonblank evidence coverage.
- [x] Make the new logical graph topology and metadata immutable after DAG
  validation, without altering the legacy graph or physical execution plan.
