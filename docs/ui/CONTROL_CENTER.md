# MERCURY X Control Center

## Purpose

The Control Center is a portfolio and research interface for understanding MERCURY X as a coherent AI compute control plane. It visualizes typed artifacts, evidence, lifecycle state, and safety boundaries across Phases 0–30 without presenting demonstration data as production telemetry.

## Architecture

The application is an isolated, dependency-free browser application under `ui/control-center/`.

```text
Views and reusable components
            ↓
ControlCenterProvider interface
            ↓
DemoControlCenterProvider (current)
            ↓
Centralized immutable demonstration snapshot

Future:
Views and reusable components
            ↓
ControlCenterProvider interface
            ↓
Dedicated MERCURY API provider
```

The browser does not import or expose Python internals. A future API adapter should translate authenticated, versioned MERCURY artifacts into the existing UI provider contract.

## Page Map

| View | MERCURY scope |
|---|---|
| Mission Control | Cross-domain workload, safety, placement, policy, twin, and evidence summary |
| Scenario Player | Six deterministic end-to-end demonstrations with lifecycle, decisions, safety, and audit evidence |
| Workloads | Request-to-execution artifact drill-down |
| Execution Graph | Logical DAG, dependencies, capabilities, context, and validation |
| Model & Precision | Exact model/revision, capabilities, composition, precision, morphing, calibration |
| Memory & Context | Session memory, global namespace context, semantic KV compatibility |
| Compute Fabric | Synthetic hardware personalities, topology, placement, and health |
| SLO & Reasoning | Quality floor, reasoning budget, protected constraints, negotiation |
| Migration & Recovery | Migration lifecycle, authority, rollback, and self-healing |
| Scheduler Intelligence | Adversarial challenges, counterfactuals, controlled policy evolution |
| Federation & Privacy | Domains, residency, authorization, privacy envelope |
| Digital Twin | Explicitly simulated and advisory scenarios |
| Governance | Evidence-to-authority supervisory decisions and human escalation |
| Evidence & Audit | Decision provenance, policy, authority, action, verification, outcome |
| System Status | Implemented, simulated, and unclaimed capability boundaries |

## Component and Data Architecture

- `src/types.js` documents the source/provenance and workload contracts with JSDoc.
- `src/data/provider.js` defines the replaceable provider boundary.
- `src/data/demo-data.js` is the single source of demonstration values.
- `src/data/demo-provider.js` returns an isolated copy of that immutable snapshot.
- `src/components.js` contains reusable panels, tables, chips, provenance badges, progress bars, and callouts.
- `src/views.js` maps the domain snapshot into all fourteen views.
- `src/app.js` owns hash navigation, workload selection, loading/error state, accessibility interactions, and provider loading.
- `src/scenarios/` owns immutable scenario definitions, deterministic playback, validation, and cross-view snapshot projection.
- `styles.css` provides the responsive dark control-plane visual system without external assets or web fonts.

## Demo-Data Provenance

Every displayed control artifact or metric is labeled as one of:

- `STATIC DEMO`
- `SYNTHETIC`
- `SIMULATED`
- `UNKNOWN`

The provider contract also reserves `LIVE` for a future authenticated adapter; the current provider does not emit live data. Provenance records include a source type, generated-at value, evidence state, calibration state, and source identifiers.

The static timestamp is snapshot metadata, not a claim of current telemetry. Synthetic utilization, health, workload, and topology values exist to demonstrate interface behavior. The digital twin is visibly `UNCALIBRATED` and `ADVISORY`.

The [end-to-end demo scenarios](DEMO_SCENARIOS.md) use deterministic logical time and the same provenance categories. The scenario contracts reject `LIVE` records.

## Backend Boundary

Currently connected:

- centralized static demonstration provider;
- repository-grounded Phase 0–30 concepts and safety invariants;
- browser-only navigation and visualization.

Potential future API connections:

- serialized workload, graph, reasoning-budget, SLO, placement, migration, and evidence artifacts;
- certification summaries;
- authorized telemetry adapters with explicit source and calibration state.

Requires future infrastructure:

- authenticated API service and authorization mapping;
- production telemetry transport;
- resource/orchestrator adapters;
- real accelerator and topology integrations;
- operational event persistence and audit storage.

## Run Locally

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m http.server 4173 --directory ui/control-center
```

Open `http://127.0.0.1:4173`.

Open `http://127.0.0.1:4173/#/scenarios` to launch the Scenario Player directly.

Alternatively:

```powershell
Set-Location ui/control-center
npm run serve
```

## Validate

No dependency installation is required.

```powershell
Set-Location ui/control-center
npm run check
```

Scenario-specific validation:

```powershell
npm.cmd run check:scenarios
```

The validator checks JavaScript syntax, required application files, navigation coverage, centralized provider loading, provenance metadata, protected safety markers, and static HTTP asset delivery.

## Current Limitations

- The UI is a static demonstration and is not connected to a MERCURY runtime or production infrastructure.
- It does not execute workloads, schedule resources, migrate device memory, or promote policy.
- Graphs and topology are HTML/SVG control-plane representations, not live distributed traces.
- No production authentication or authorization adapter is present.
- No empirical performance, accelerator, thermal, power, or quality claims are made.
- Browser validation covers module syntax and static asset delivery; a future production UI could add browser automation and visual-regression testing.

## Safety and Claim Boundaries

- There is no silent quality degradation path.
- UNKNOWN, DEFER, REJECT, and ESCALATE remain explicit.
- Policy promotion stops at human approval.
- Migration shows exactly one authoritative executor and a rollback path.
- The digital twin is advisory and uncalibrated.
- Physical GPU/VM memory migration is not depicted as implemented.
- Simulation and synthetic evidence are never labeled live.
