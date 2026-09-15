# Benchmark Workloads Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Define a reproducible, CPU-safe benchmark workload catalog covering MERCURY X core workload classes without recording synthetic performance as measured evidence.

**Architecture:** Add a small benchmark-definition layer that composes the certified WorkloadRequest and WorkloadProfile contracts. A JSON catalog supplies canonical scenarios; validation checks unique IDs, required categories, CPU-safe coverage, and explicit remote-GPU eligibility without performing scheduling.

**Tech Stack:** Python 3.13, Pydantic v2, pytest, JSON.

**Spec:** `docs/MERCURY_X_MASTER_SPEC.md`

## Global Constraints
- Preserve strict SIMULATED vs MEASURED separation.
- Local development must remain CPU-first.
- Remote GPU is an allowed execution mode, never assumed locally available.
- Benchmark definitions contain no performance results.
- Do not add scheduling or placement decisions in this step.

---

### Task 1: Benchmark definition contracts and catalog
**Files:**
- Create: `src/mercury/benchmark/models.py`
- Create: `src/mercury/benchmark/catalog.py`
- Create: `src/mercury/benchmark/__init__.py`
- Create: `configs/benchmarks/workloads.json`
- Test: `tests/test_benchmark_workloads.py`

**Interfaces:**
- Consumes: `WorkloadRequest`, `WorkloadProfile`
- Produces: `BenchmarkDefinition`, `BenchmarkCatalog`, `load_benchmark_catalog`

- [ ] Step 1: Write tests for coverage, identity consistency, CPU/remote-GPU modes, and absence of measured results.
- [ ] Step 2: Run tests and confirm RED because `mercury.benchmark` does not exist.
- [ ] Step 3: Implement the minimal benchmark models/catalog/loader and canonical JSON workload definitions.
- [ ] Step 4: Run focused benchmark tests and confirm GREEN.

- [ ] Step 5: Run Step 3–6 regression tests.

## Current Verification

The unchecked historical implementation log has no preserved RED-run output,
so it is intentionally not retroactively marked complete. Fresh preflight
remediation verification confirms the checked-in benchmark catalog and its
behavior:

- [x] `tests/test_benchmark_workloads.py` passed in the project-local venv.
- [x] The complete `.venv\\Scripts\\python.exe -m pytest tests -v` suite
  reported 61 passed.
- [x] `configs/benchmarks/workloads.json` remains definition-only; no simulated
  or measured performance result is stored in the benchmark definitions.
