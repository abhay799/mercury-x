# Contributing to MERCURY X

MERCURY X is an experimental AI compute control-plane research project. Contributions should strengthen deterministic behavior, evidence quality, safety invariants, reproducibility, or the clarity of the research boundary.

## Before changing code

1. Read [the architecture](docs/architecture/MERCURY_X_ARCHITECTURE.md), [phase index](docs/architecture/PHASE_INDEX.md), and [safety invariants](docs/architecture/SAFETY_INVARIANTS.md).
2. Follow the local setup in [RUNNING.md](docs/RUNNING.md).
3. Keep changes within the owning phase or productization surface. Do not move responsibilities across phase boundaries without an approved design.
4. Use test-driven development for behavior changes: demonstrate RED, implement the minimum GREEN change, then refactor while focused tests remain green.

## Required engineering behavior

- Preserve exact identity, generation, version, and provenance across handoffs.
- Fail closed on unknown, stale, malformed, contradictory, or unauthorized hard state.
- Never silently weaken quality, safety, verification, authorization, privacy, residency, or an agreed SLO.
- Keep counterfactual and digital-twin output advisory unless a separately authorized execution path exists.
- Preserve exactly one authoritative executor through migration cutover.
- Require explicit evidence and human authority for controlled policy promotion.
- Avoid hidden ranking, preference, fallback, placement, or runtime semantics in phases that do not own them.

## Validation

Run the narrowest relevant test first, then the affected integration/certification checks. Before requesting review, run the Windows-safe full regression when Python runtime, tests, certification, packaging behavior, or dependencies changed:

```powershell
$stamp = Get-Date -Format "yyyyMMddHHmmss"
$bt = Join-Path $env:TEMP "mercury-pytest-$stamp"
$cache = Join-Path $env:TEMP "mercury-cache-$stamp"
.\.venv\Scripts\python.exe -m pytest tests -q --basetemp="$bt" -o cache_dir="$cache"
```

For documentation or static UI changes, run their focused validators and explain why a full Python regression was or was not required. See [VALIDATION.md](docs/VALIDATION.md).

## Evidence and claims

Classify evidence as `MEASURED`, `SYNTHETIC`, `SIMULATED`, `STATIC_DEMO`, `UNCALIBRATED`, or `NOT_MEASURED`. Every quantitative claim needs provenance, environment, method, and scope. Do not present tests as benchmarks, simulation as measurement, static fixtures as live telemetry, logical migration as physical migration, or control-plane research as production deployment.

## Pull requests

Keep changes reviewable and describe:

- the invariant or documentation outcome;
- files and phase boundaries affected;
- focused and regression commands run;
- evidence classification;
- safety and claim-boundary impact;
- unresolved limitations.

This repository does not currently include a license file. Do not infer reuse rights from repository visibility; licensing remains an explicit owner decision.
