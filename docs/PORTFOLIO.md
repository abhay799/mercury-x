# MERCURY X Portfolio Page

## Purpose

The portfolio page explains the engineering problem, Phase 0–30 architecture, control lifecycle, safety model, demonstration scenarios, verified evidence, and explicit limitations to a technical reviewer. It complements rather than replaces the Control Center:

- the **portfolio** explains the project and its engineering significance;
- the **Control Center** demonstrates deterministic system and scenario state.

The page is an isolated dependency-free static surface under `ui/portfolio/`. It does not import MERCURY runtime code or issue infrastructure commands.

## Run locally

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m http.server 4174
```

Open `http://127.0.0.1:4174/ui/portfolio/` and stop the server with `Ctrl+C`.

Validate the page from `ui/portfolio/`:

```powershell
npm.cmd run check
```

No `npm install` is required.

## Content and evidence sources

The page is grounded in maintained repository artifacts:

- `README.md` for product identity and scope;
- `docs/architecture/` for phase grouping, lifecycle, and invariants;
- `docs/ui/DEMO_SCENARIOS.md` for the six deterministic scenarios;
- `docs/evidence/BENCHMARKS_AND_EVIDENCE.md` for verified counts and classifications;
- `docs/LIMITATIONS.md` for unsupported deployment and performance claims.

Evidence values must be updated only when the committed evidence report is updated from a fresh verified run. Command duration is not displayed as system performance.

## Claim boundaries

The portfolio must preserve these distinctions:

- control-plane implementation is not production deployment;
- `STATIC_DEMO` is not live telemetry;
- `SYNTHETIC` and `SIMULATED` are not infrastructure measurements;
- `UNCALIBRATED` output does not establish predictive accuracy;
- logical migration is not physical GPU or VM-memory migration;
- controlled policy evolution is not autonomous production promotion.

## Hosting

The page can be served by any static host whose root includes the repository layout so its relative documentation and Control Center links remain available. No public hosting URL is currently claimed. A future hosted deployment should add a link only after the endpoint exists and the same validation and claim-safety checks pass.
