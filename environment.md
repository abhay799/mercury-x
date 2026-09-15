# MERCURY X Environment Baseline

Status: PRE-DEVELOPMENT BASELINE

## Project
- Name: MERCURY X — Autonomous Cognitive Compute Fabric
- Development OS: Windows
- Primary shell: PowerShell
- IDE: Visual Studio Code
- Environment strategy: one project-local `.venv`

## Verified Runtime
- Python: 3.13.9
- pytest: 9.1.1
- pluggy: 1.6.0
- pytest-asyncio: 1.4.0
- setuptools: 84.0.0 (pinned build prerequisite)
- Project package: `mercury-x 0.0.0` installed editable from this repository

## Verified Baseline Tests
- `tests/test_execution_graph.py` — PASS
- `tests/test_workload.py` — PASS
- Baseline result: 2 passed

## Current Verification

The two-test result above is historical only. The current preflight regression
total is recorded only after a fresh full-suite run in the certification
record. Focused environment verification includes a direct root-level
`import mercury` subprocess check without pytest path injection.

Current preflight remediation result: `61 passed` via
`.\.venv\Scripts\python.exe -m pytest tests -v`.

## Setup / Refresh

`requirements.txt` is the canonical pinned dependency lock for this
pre-development baseline. Use the repository-local interpreter; do not rely on
the system Python installation.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install --no-deps --no-build-isolation -e .
```

The editable install makes the `src/mercury` package importable from the
repository root without relying on pytest's `pythonpath` setting.

## Execution Strategy
MERCURY X is CPU-first for local development and control-plane work.
GPU execution is abstracted behind worker/provider interfaces so later phases can use
local GPU, remote GPU, Kaggle/Colab, or cloud resources without changing core contracts.

## Environment Rules
1. Use `.venv` for this repository.
2. Do not commit `.venv`.
3. Do not commit secrets, API keys, credentials, tokens, or private endpoints.
4. Update the dependency lock whenever project dependencies intentionally change.
5. Record measured hardware/runtime results separately from simulated results.
6. Re-run the baseline test suite after environment changes.

## Revalidation
```powershell
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pip --version
.\.venv\Scripts\python.exe -c "import mercury; print(mercury.__file__)"
.\.venv\Scripts\python.exe -m pytest tests -v
```
