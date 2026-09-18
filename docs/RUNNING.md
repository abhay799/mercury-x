# Running MERCURY X

## Prerequisites

The supported local research path is CPU-first and requires:

- Windows with PowerShell (primary path), or a shell with equivalent Python commands;
- Python 3.13;
- Git;
- Node.js/npm for Control Center validation;
- no GPU, cloud account, paid API, or external service.

The Control Center itself is dependency-free and uses browser-native JavaScript modules. npm is used only to expose its validation commands.

## Windows PowerShell setup

The public clone URL is not recorded in this repository. Substitute the actual URL supplied by the repository owner:

```powershell
git clone <repository-url>
cd Mercury-x
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install --no-deps --no-build-isolation -e .
.\.venv\Scripts\python.exe -c "import mercury; print(mercury.__file__)"
```

Using the interpreter by full path avoids PowerShell execution-policy issues around `Activate.ps1`. Optional activation is:

```powershell
.\.venv\Scripts\Activate.ps1
```

Do not store credentials in the repository. The baseline commands perform no external service calls.

## Portable setup

On a platform with Python 3.13 available as `python3.13`:

```bash
git clone <repository-url>
cd Mercury-x
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install --no-deps --no-build-isolation -e .
.venv/bin/python -c "import mercury; print(mercury.__file__)"
```

The repository is developed and freshly validated on Windows; portable commands do not imply that every platform has been measured.

## Relevant repository structure

| Path | Purpose |
|---|---|
| `src/mercury/` | CPU-first control-plane contracts and deterministic engines |
| `tests/` | Unit, integration, adversarial, compatibility, and certification tests |
| `configs/certification/` | Per-phase internal certification manifests |
| `scripts/evidence/` | Evidence validation and local snapshot generation |
| `ui/control-center/` | Dependency-free static Control Center and scenario player |
| `docs/evidence/` | Evidence taxonomy, inventory, interpretation, and boundaries |

## Core validation

Focused example:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_phase30_platform.py -q
```

Full Windows-safe regression:

```powershell
$stamp = Get-Date -Format "yyyyMMddHHmmss"
$bt = Join-Path $env:TEMP "mercury-pytest-$stamp"
$cache = Join-Path $env:TEMP "mercury-cache-$stamp"
.\.venv\Scripts\python.exe -m pytest tests -q --basetemp="$bt" -o cache_dir="$cache"
```

The temporary and cache directories are outside the repository to avoid Windows file-locking and cleanup interference.

## Certifications

Each numbered phase has a repository-internal manifest and evaluator. For example:

```powershell
.\.venv\Scripts\python.exe -m mercury.certification.phase30
```

Certification-focused regression:

```powershell
$certTests = Get-ChildItem tests -Filter "test_phase*_certification.py" | ForEach-Object FullName
.\.venv\Scripts\python.exe -m pytest @certTests -q
```

These commands validate internal architecture and completeness. They are not external, regulatory, security, or industry certification.

## Evidence generation

Validate the maintained evidence taxonomy, manifest, report, and runner:

```powershell
.\.venv\Scripts\python.exe scripts\evidence\validate_evidence.py
```

Generate a complete local evidence snapshot:

```powershell
.\.venv\Scripts\python.exe scripts\evidence\run_evidence.py
```

The generated, Git-ignored output is `artifacts/evidence/mercury_evidence.json`. It records the commit, coarse environment, commands, classifications, results, durations, and claim boundary.

For a shorter check without a current full-regression claim:

```powershell
.\.venv\Scripts\python.exe scripts\evidence\run_evidence.py --skip-python-tests
```

See [BENCHMARKS_AND_EVIDENCE.md](evidence/BENCHMARKS_AND_EVIDENCE.md) before interpreting any output.

## Control Center

Start the dependency-free static application from the repository root:

```powershell
.\.venv\Scripts\python.exe -m http.server 4173 --directory ui/control-center
```

Open `http://127.0.0.1:4173` and stop the server with `Ctrl+C`.

Validate the UI from `ui/control-center/`:

```powershell
npm.cmd run check
npm.cmd run check:scenarios
```

On non-Windows shells, use `npm run check` and `npm run check:scenarios`.

## Demo scenarios

Open the **Scenario Player** view in the Control Center. The six scenarios are deterministic and fixture-backed. Controls advance or reset logical steps; they do not issue commands to infrastructure. See [DEMO_SCENARIOS.md](ui/DEMO_SCENARIOS.md).

## Troubleshooting

- **`python` resolves to the wrong interpreter:** use `.\.venv\Scripts\python.exe` explicitly.
- **Editable import fails:** rerun `pip install --no-deps --no-build-isolation -e .` using the local interpreter.
- **PowerShell blocks activation:** activation is optional; use the full interpreter path.
- **npm is unavailable:** install a supported Node.js distribution. No `npm install` is required for the current UI.
- **Port 4173 is occupied:** choose another local port and open the matching URL.
- **Evidence snapshot reports `dirty: true`:** preserve the status as context or generate from a clean checkpoint; do not relabel it.
- **A command fails:** treat the snapshot as failed evidence. Do not delete failed checks or convert them to `PASS`.

## Runtime boundaries

The baseline runs local control-plane logic, tests, internal certification, static demonstrations, and simulations. It does not provide physical GPU execution, live GPU-memory migration, distributed cloud deployment, calibrated datacenter prediction, production federation, hardware-backed privacy, or autonomous datacenter control.

Synthetic and simulated output must remain labeled. Logical migration is not physical memory migration; policy research is not autonomous production optimization; and a static dashboard is not live telemetry.

## Optional and future infrastructure

GPU workers, remote providers, distributed stores, cloud deployment, real telemetry adapters, and calibrated models are optional future integrations. They are not prerequisites for the local reviewer journey and should be evaluated with separate credentials, safety review, benchmarks, and evidence.
