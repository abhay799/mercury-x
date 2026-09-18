# MERCURY X Demo Video Script

## Overview

| Property | Value |
|---|---|
| **Duration** | ~5 minutes (4:50) |
| **Format** | Screen recording with narration |
| **Audience** | Engineers, hiring managers, portfolio reviewers |
| **Tone** | Technically credible, unhurried, honest about scope |
| **Surfaces** | Portfolio page, Control Center |

The script tells one engineering story: a workload enters the system, progresses through every major decision boundary, encounters resource pressure, migrates, is challenged adversarially, and completes under human-governed control—all with provenance visible.

---

## Opening — Problem + Architecture (0:00–0:50)

### 0:00–0:25 — Problem statement

| Property | Value |
|---|---|
| **Screen** | Portfolio page hero section (`ui/portfolio/`) |
| **User action** | Page loads; no interaction yet |
| **Narration** | "Modern AI execution is more than choosing a model. A control plane has to reconcile model capability, compute availability, quality requirements, context, topology, privacy, failures, and policy—often with incomplete or contradictory evidence. MERCURY X explores how those constraints can be coordinated without turning missing evidence into permission." |
| **Important visual** | Hero copy, orbit visualization, "Research / Experimental" chip, boundary note |
| **Concept demonstrated** | The coupled control problem that motivates the project |

### 0:25–0:50 — Architecture overview

| Property | Value |
|---|---|
| **Screen** | Portfolio page — scroll to architecture section |
| **User action** | Scroll to "Nine layers. One governed lifecycle." Open first two layer cards |
| **Narration** | "MERCURY implements thirty-one numbered phases organized into nine architectural layers—from workload intelligence and model adaptation through memory, placement, reasoning, migration, scheduling, federation, and supervisory control. Each phase accepts explicit inputs, preserves provenance, and exposes a failure state. This is a research-oriented, CPU-first control-plane implementation. It does not claim a production datacenter deployment." |
| **Important visual** | Layer grid with phase ranges; "Research / Experimental" chip still visible in header |
| **Concept demonstrated** | Scope, layered architecture, and explicit boundary |

---

## Control Center Entry — Mission Control (0:50–1:20)

### 0:50–1:20 — First look

| Property | Value |
|---|---|
| **Screen** | Control Center overview (`ui/control-center/#/overview`) |
| **User action** | Navigate from portfolio "Explore the Control Center" button; page loads |
| **Narration** | "The Control Center is a provenance-first interface. Every artifact displayed here declares whether it is static demonstration data, synthetic, simulated, or unknown. The mode banner confirms no live infrastructure is connected. The overview shows tracked workloads, hard invariants, certified phases, the current control path, and recent traceable decisions." |
| **Important visual** | Mode banner ("STATIC DEMO · No live infrastructure"), source legend, metric grid, invariant watch, control path flow |
| **Concept demonstrated** | Provenance-first design; no hidden data sources |

---

## Workload Intelligence (1:20–1:50)

### 1:20–1:50 — Workload enters the system

| Property | Value |
|---|---|
| **Screen** | Workloads view (`#/workloads`) |
| **User action** | Click workload tab `wrk-7f2a` (Document reasoning) |
| **Narration** | "Let's follow a workload. A document reasoning request enters through the cognitive gateway. MERCURY classifies it, assigns an intelligence SLO, builds an execution graph, resolves model and precision requirements, and determines placement—all as deterministic, traceable control artifacts. Every field here—modality, quality floor, model identity, precision profile—has provenance back to the originating evidence." |
| **Important visual** | Workload detail panel with all fields; provenance badge; decision path flow |
| **Concept demonstrated** | Evidence-backed workload lifecycle; exact identity preservation |

---

## Execution Graph + Model Decision (1:50–2:20)

### 1:50–2:05 — Execution graph

| Property | Value |
|---|---|
| **Screen** | Execution Graph view (`#/graph`) |
| **User action** | Navigate via sidebar |
| **Narration** | "The execution graph is a validated logical DAG—not a deployed pipeline. Input flows through retrieval, reasoning, validation, and structured output. Each node declares its capability requirement, placement, and context reference. The graph safeguards confirm acyclic topology, no dangling edges, and verified capability coverage." |
| **Important visual** | Five-node DAG with state chips; safeguards panel with VERIFIED checks |
| **Concept demonstrated** | Deterministic graph before resource commitment |

### 2:05–2:20 — Model and precision

| Property | Value |
|---|---|
| **Screen** | Model & Precision view (`#/models`) |
| **User action** | Navigate via sidebar |
| **Narration** | "Model selection uses exact identity and revision, not a hidden ranking score. The precision profile is a registered compatibility artifact. Both are explicitly UNCALIBRATED—the repository tests selection logic and safety boundaries, not empirical model quality." |
| **Important visual** | Composition profile table; calibration honesty callout; non-authority guards |
| **Concept demonstrated** | Honest calibration; no hidden ranking |

---

## Placement + SLO Negotiation (2:20–3:00)

### 2:20–2:35 — Compute fabric

| Property | Value |
|---|---|
| **Screen** | Compute Fabric view (`#/compute`) |
| **User action** | Navigate via sidebar |
| **Narration** | "The compute fabric shows synthetic resource personalities and a generation-aware topology. Nodes have health, utilization, and placement counts—but these are not live telemetry. The interface explicitly says 'not live telemetry' because honest labeling is a design requirement, not an afterthought." |
| **Important visual** | Topology canvas; "NOT LIVE TELEMETRY" eyebrow; infrastructure boundary callout |
| **Concept demonstrated** | Synthetic topology; honest labeling |

### 2:35–3:00 — SLO quality conflict scenario

| Property | Value |
|---|---|
| **Screen** | SLO & Reasoning view (`#/slo`) |
| **User action** | From the Scenario Player (`#/scenarios`), select the "Quality / SLO conflict" scenario, start it, advance to step 4 ("Hard conflict detected"), then navigate to `#/slo` |
| **Narration** | "Now let's see what happens under resource pressure. This scenario requests a quality floor of 0.92, but only 18 of 31 logical resource units are available. A cheaper path would lower quality—MERCURY detects this as a hard conflict and rejects it. The system issues a counteroffer that changes only negotiable constraints and requires explicit approval. Quality, verification depth, and safety are protected and cannot be silently degraded." |
| **Important visual** | Scenario conflict callout; metric cards; protected constraints with ENFORCED chips; "NO SILENT QUALITY DEGRADATION" eyebrow |
| **Concept demonstrated** | Core safety invariant: reject silent degradation |

---

## Migration + Recovery (3:00–3:30)

### 3:00–3:30 — Live migration scenario

| Property | Value |
|---|---|
| **Screen** | Migration & Recovery view (`#/migration`) |
| **User action** | From Scenario Player, select "Live workload migration", advance to step 8 ("Equivalence verification"), navigate to `#/migration` |
| **Narration** | "MERCURY orchestrates a logical migration from Node A to Node B. The timeline shows ten stages—checkpoint, transfer, restore, verify, cutover. The authority lock guarantees exactly one authoritative executor at every point. Node A remains authoritative until verified atomic cutover. If verification fails, rollback is armed. This is a simulated control-plane migration—we do not claim physical GPU or VM live-memory transfer." |
| **Important visual** | Stage timeline; authority lock panel; preserved control-state tags; SIMULATED provenance badges |
| **Concept demonstrated** | Migration authority invariant; explicit physical-claim boundary |

---

## Adversarial Scheduling + Federation (3:30–4:05)

### 3:30–3:50 — Adversarial challenge

| Property | Value |
|---|---|
| **Screen** | Scheduler Intelligence view (`#/scheduler`) |
| **User action** | Select "Adversarial scheduling + counterfactual" scenario, advance to step 5, navigate to `#/scheduler` |
| **Narration** | "The adversarial system challenges scheduling decisions for starvation pressure and stale evidence. Counterfactual alternatives are generated for comparison—but they remain advisory and uncalibrated. They cannot directly authorize execution. Policy evolution follows a controlled path from offline through shadow, canary, human approval, and promotion. Autonomous promotion is explicitly forbidden." |
| **Important visual** | Challenge cards; counterfactual alternatives with VALID/INVALID; policy evolution flow with "HUMAN APPROVAL" highlighted; "NOT PROMOTED" chip |
| **Concept demonstrated** | Advisory-only alternatives; human-governed policy |

### 3:50–4:05 — Federation and privacy

| Property | Value |
|---|---|
| **Screen** | Federation & Privacy view (`#/federation`) |
| **User action** | Select "Federated privacy / residency" scenario, advance to step 6, navigate to `#/federation` |
| **Narration** | "Federated execution domains are filtered by residency, authorization, purpose, and minimum-necessary access. The EU domain is rejected for residency mismatch. The research domain is rejected for insufficient authority. Only the compliant edge domain is selected. The privacy envelope enforces fail-closed behavior—insufficient evidence cannot broaden access." |
| **Important visual** | Domain table with DENIED/EXCLUDED chips; privacy seal with "FAIL CLOSED" |
| **Concept demonstrated** | Residency and privacy enforcement |

---

## Digital Twin + Governance (4:05–4:30)

### 4:05–4:15 — Digital twin

| Property | Value |
|---|---|
| **Screen** | Digital Twin view (`#/twin`) |
| **User action** | Navigate via sidebar (default state) |
| **Narration** | "The datacenter digital twin is explicitly uncalibrated. It models what-if scenarios—but it cannot authorize action. The danger callout states this directly. Simulated alternatives show effects and confidence levels, but with no production side effects. Honest calibration state is an engineering choice." |
| **Important visual** | Danger callout; UNCALIBRATED/ADVISORY chips; "NO PRODUCTION SIDE EFFECTS" eyebrow |
| **Concept demonstrated** | Simulation boundary; calibration honesty |

### 4:15–4:30 — Governance and evidence

| Property | Value |
|---|---|
| **Screen** | Governance (`#/governance`) then Evidence & Audit (`#/evidence`) |
| **User action** | Navigate to governance, pause, then navigate to evidence |
| **Narration** | "Governance decisions pass through evidence, authority, safety invariants, and human escalation before execution authorization. Unknown, defer, and escalate are first-class outcomes—not error states. The evidence audit shows every decision with its provenance chain: evidence, policy, authority, action, verification, and outcome. This is a demonstration view, not an external compliance attestation." |
| **Important visual** | Decision pipeline flow; supervisory decisions with UNKNOWN/DEFER/ESCALATE; evidence ledger rows with provenance |
| **Concept demonstrated** | Human control; complete traceability |

---

## Closing — Evidence + Boundary (4:30–4:50)

### 4:30–4:50 — System status and closing

| Property | Value |
|---|---|
| **Screen** | System Status view (`#/system`) |
| **User action** | Navigate via sidebar |
| **Narration** | "The system status view shows the claim matrix: control-plane logic is implemented, synthetic fixtures are available, counterfactual and twin output is simulated and advisory. Production infrastructure adapters are not connected. Real GPU live migration is not claimed. Autonomous policy promotion is forbidden. MERCURY X is a research-oriented control-plane architecture with 31 implemented phases, over 1500 passing tests, and six deterministic demo scenarios. It demonstrates how AI execution can be reasoned about as one evidence-bound system—with honest boundaries about what it is and what it is not." |
| **Important visual** | Claim matrix with IMPLEMENTED / NOT CONNECTED / NOT CLAIMED / FORBIDDEN chips; repository state panel |
| **Concept demonstrated** | Explicit claim boundary; engineering credibility |

---

## Production notes

- **Total narration:** approximately 1450 words at a measured pace (~290 words/minute) fits within 5 minutes.
- **Scenario resets:** Reset each scenario before advancing to the specified step. See [RECORDING_GUIDE.md](RECORDING_GUIDE.md) for procedure.
- **Transitions:** Allow 2–3 seconds of silence during view transitions for visual breathing room.
- **Cursor:** Move the cursor deliberately to guide the viewer's eye. Avoid rapid or nervous mouse movement.
- **Scrolling:** Scroll slowly and predictably. Pause on panels before narrating their content.
- **Editing:** The raw recording will likely be 7–9 minutes. Edit for pacing, not for content removal. Do not edit out provenance labels or boundary callouts.

## Claim-safety checklist

Before publishing, verify the final recording does not:

- [ ] Imply production deployment
- [ ] Claim real autonomous datacenter operation
- [ ] Claim physical GPU or VM live-memory migration
- [ ] Present the digital twin as calibrated
- [ ] Present the scheduler as a trained production system
- [ ] Claim connected distributed or cloud runtime
- [ ] Hide STATIC DEMO, SYNTHETIC, SIMULATED, or UNKNOWN labels
- [ ] Present test counts as performance benchmarks
- [ ] Present command durations as system throughput
