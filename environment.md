# MERCURY X Environment

## Current supported local research environment

MERCURY X is developed and validated as a CPU-first control plane. The primary environment is:

- Windows with PowerShell;
- Python 3.13 (`>=3.13,<3.14` in package metadata);
- a repository-local `.venv`;
- dependencies pinned by `requirements.txt`;
- an editable installation of this repository;
- Node.js/npm for dependency-free Control Center validation.

The environment observed during this productization pass is Python 3.13.9 and npm 11.16.0. That observation is `MEASURED` environment context, not a portability or performance claim.

## Setup and refresh

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install --no-deps --no-build-isolation -e .
.\.venv\Scripts\python.exe -c "import mercury; print(mercury.__file__)"
```

Use the repository-local interpreter rather than relying on system Python. See [docs/RUNNING.md](docs/RUNNING.md) for validation, certification, evidence, and Control Center commands.

## Current validation practice

Fresh results are generated rather than copied from historical documentation:

```powershell
.\.venv\Scripts\python.exe scripts\evidence\run_evidence.py
```

The generated snapshot is local, machine-readable evidence and remains Git-ignored. Historical test totals are not treated as current measurements.

## Environment rules

1. Do not commit `.venv`, caches, generated evidence snapshots, secrets, credentials, tokens, or private endpoints.
2. Update `requirements.txt` when dependencies intentionally change.
3. Record measured results separately from synthetic, simulated, static-demo, uncalibrated, and not-measured evidence.
4. Run the full regression after environment or packaging changes.
5. Keep the default reviewer journey CPU-local and free of external service requirements.

## Future and optional infrastructure environments

GPU workers, remote accelerators, Kaggle/Colab, cloud resources, distributed stores, telemetry adapters, and multi-datacenter deployments are optional integrations outside the supported local baseline. Their interfaces do not prove deployment, throughput, scaling, migration downtime, cost, power, model-quality, or federation performance.

Any future infrastructure result requires its own environment record, workload, method, evidence classification, and claim boundary. A local GPU is not required for baseline setup or validation.

## Historical note

Earlier revisions described a pre-development environment and small historical test totals. Those records described their checkpoints only and are not current evidence. Git history preserves them if needed.
