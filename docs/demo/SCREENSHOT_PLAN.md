# MERCURY X Screenshot Plan

## Purpose

This plan defines the exact screenshots needed to present MERCURY X to engineers, recruiters, hiring managers, and portfolio reviewers. Each capture is chosen to demonstrate a distinct architectural capability while preserving provenance and claim-boundary labels.

## General capture rules

1. **Do not crop or hide** `STATIC DEMO`, `SYNTHETIC`, `SIMULATED`, or `UNKNOWN` provenance labels. They are engineering credibility markers, not blemishes.
2. Keep the sidebar mode banner ("STATIC DEMO · No live infrastructure") visible unless the crop intentionally focuses on a single panel.
3. Use the dark theme as shipped—no custom browser overrides.
4. Capture at **1920 × 1080** or **2560 × 1440** for crisp retina display. See [RECORDING_GUIDE.md](RECORDING_GUIDE.md) for browser preparation.
5. Reset scenarios before capture to ensure deterministic state.

---

## Screenshot 01 — Mission Control Overview

| Property | Value |
|---|---|
| **View** | `#/overview` (Mission Control) |
| **Scenario state** | No scenario active; default snapshot |
| **What should be visible** | Metric grid (tracked workloads, hard invariants, certified phases, authoritative executors), source legend, demonstration boundary callout, workload control-state table, invariant watch panel, control path flow, recent decisions table |
| **Why it matters** | First impression of the entire system—shows breadth, provenance awareness, and fail-closed posture at a glance |
| **Recommended framing** | Full viewport capture; sidebar visible with brand mark, mode banner, and navigation |
| **Must-remain-visible labels** | Mode banner: "STATIC DEMO · No live infrastructure"; source legend chips; provenance badges on every metric and table row |
| **Portfolio / GitHub use** | Hero image for README, portfolio header, LinkedIn post |

---

## Screenshot 02 — Workload Intelligence Detail

| Property | Value |
|---|---|
| **View** | `#/workloads` |
| **Scenario state** | No scenario; select workload `wrk-7f2a` (Document reasoning) |
| **What should be visible** | Workload tabs with wrk-7f2a selected, control artifact panel (ID, modality, state, quality floor, model, precision, placement, reasoning budget, SLO, negotiation), provenance detail panel, workload decision path |
| **Why it matters** | Demonstrates the evidence-backed path from canonical request to execution state with exact identity and provenance |
| **Recommended framing** | Full viewport; workload tabs and detail panels visible |
| **Must-remain-visible labels** | SYNTHETIC provenance badge on workload; "PHASE HANDOFFS" eyebrow |
| **Portfolio / GitHub use** | Architecture deep-dive, "how MERCURY reasons about workloads" |

---

## Screenshot 03 — Execution Graph DAG

| Property | Value |
|---|---|
| **View** | `#/graph` |
| **Scenario state** | Default (graph-wrk-7f2a-v3) |
| **What should be visible** | Five-node DAG (Input → Retrieval → Reasoning → Validation → Output) with capability/model, placement, context per node; dependency contract table; graph safeguards with all five VERIFIED checks |
| **Why it matters** | Shows the deterministic logical graph before any resource commitment—core architectural differentiator |
| **Recommended framing** | Full viewport or crop to DAG + safeguards panels |
| **Must-remain-visible labels** | SYNTHETIC provenance badge; "placement labels are control artifacts, not proof of distributed execution" header text |
| **Portfolio / GitHub use** | Technical architecture illustration, engineering portfolio |

---

## Screenshot 04 — Compute Fabric & Topology

| Property | Value |
|---|---|
| **View** | `#/compute` |
| **Scenario state** | Start the `normal-orchestration` scenario, advance to step 8 ("Topology evaluation") |
| **What should be visible** | SVG topology canvas with four nodes (edge-a, core-b, core-c degraded, archive-d), dashed links, health/utilization progress bars, scenario banner showing active demonstration, infrastructure boundary callout |
| **Why it matters** | Visual topology with synthetic resource personalities, generation-aware placement evidence, and explicit "NOT LIVE TELEMETRY" label |
| **Recommended framing** | Full viewport; topology canvas and resource state side by side |
| **Must-remain-visible labels** | "NOT LIVE TELEMETRY" eyebrow; "SYNTHETIC LOGICAL TOPOLOGY" eyebrow; GENERATION 42 chip; infrastructure boundary callout; scenario banner |
| **Portfolio / GitHub use** | Visual portfolio highlight, system architecture presentation |

---

## Screenshot 05 — SLO, Reasoning & Negotiation (Quality Conflict)

| Property | Value |
|---|---|
| **View** | `#/slo` |
| **Scenario state** | Select `quality-slo-conflict` scenario, advance to step 4 ("Hard conflict detected") |
| **What should be visible** | Scenario conflict callout (quality 0.92 preserved, only 18 of 31 units available), quality/confidence/verification metric cards, reasoning budget bars, protected constraints shield grid with ENFORCED chips, negotiation boundary flow |
| **Why it matters** | Demonstrates that MERCURY rejects silent quality degradation and issues explicit counteroffers—a core safety invariant |
| **Recommended framing** | Full viewport; conflict callout and protected constraints both visible |
| **Must-remain-visible labels** | Scenario banner with "ACTIVE DEMONSTRATION SCENARIO"; "NO SILENT QUALITY DEGRADATION" eyebrow; ENFORCED chips; SYNTHETIC/SIMULATED provenance badges |
| **Portfolio / GitHub use** | Safety model highlight, "how MERCURY handles resource pressure" |

---

## Screenshot 06 — Migration & Recovery with Authority Lock

| Property | Value |
|---|---|
| **View** | `#/migration` |
| **Scenario state** | Select `live-migration` scenario, advance to step 8 ("Equivalence verification") |
| **What should be visible** | Migration stage timeline with steps through VERIFY, authority/rollback panel with "Exactly one authoritative executor" lock, preserved control-state tags, self-healing lifecycle panel |
| **Why it matters** | Shows verified cutover with rollback protection and authority invariant—without claiming physical GPU memory transfer |
| **Recommended framing** | Full viewport; timeline and authority lock both visible |
| **Must-remain-visible labels** | SIMULATED provenance badges; "Verified cutover and bounded healing without claiming physical GPU or VM live-memory transfer" header; "CUTOVER INVARIANT" eyebrow; authority lock text |
| **Portfolio / GitHub use** | Resilience engineering, migration architecture |

---

## Screenshot 07 — Scheduler Intelligence & Counterfactual

| Property | Value |
|---|---|
| **View** | `#/scheduler` |
| **Scenario state** | Select `adversarial-counterfactual` scenario, advance to step 5 ("Advisory comparison") |
| **What should be visible** | Adversarial challenges panel (starvation, stale topology), counterfactual alternatives panel with VALID/INVALID outcomes and uncertainty, controlled policy evolution flow with human approval gate |
| **Why it matters** | Demonstrates adversarial challenge, advisory-only alternatives, and the explicit human promotion gate |
| **Recommended framing** | Full viewport; challenges, alternatives, and policy evolution all visible |
| **Must-remain-visible labels** | SIMULATED provenance on counterfactuals; "PHASE 24 · ADVISORY" eyebrow; "NOT PROMOTED" chip; human promotion gate callout |
| **Portfolio / GitHub use** | Scheduler intelligence, safety engineering |

---

## Screenshot 08 — Federation & Privacy

| Property | Value |
|---|---|
| **View** | `#/federation` |
| **Scenario state** | Select `federated-privacy` scenario, advance to step 6 ("Compliant candidate selected") |
| **What should be visible** | Federated execution domains table with ELIGIBLE/DENIED/RESTRICTED states, privacy envelope panel with fail-closed seal, scenario banner |
| **Why it matters** | Shows residency, authorization, purpose, and minimum-necessary access enforcement |
| **Recommended framing** | Full viewport; domain table and privacy seal both visible |
| **Must-remain-visible labels** | SYNTHETIC provenance badges; "FAIL CLOSED" seal; DENIED and EXCLUDED chips on rejected domains |
| **Portfolio / GitHub use** | Privacy engineering, compliance architecture |

---

## Screenshot 09 — Digital Twin (Advisory / Uncalibrated)

| Property | Value |
|---|---|
| **View** | `#/twin` |
| **Scenario state** | Default (twin-scenario-03) |
| **What should be visible** | "Not a calibrated production twin" danger callout, scenario definition with UNCALIBRATED/ADVISORY status, scenario inputs, simulated alternatives with confidence states, "NO PRODUCTION SIDE EFFECTS" eyebrow |
| **Why it matters** | Demonstrates honest calibration state—explicitly UNCALIBRATED and advisory, a credibility differentiator |
| **Recommended framing** | Full viewport; danger callout and alternatives panel both visible |
| **Must-remain-visible labels** | SIMULATED provenance; UNCALIBRATED chip; ADVISORY chip; danger callout text |
| **Portfolio / GitHub use** | Simulation architecture, claim honesty |

---

## Screenshot 10 — Scenario Player (Normal Orchestration)

| Property | Value |
|---|---|
| **View** | `#/scenarios` |
| **Scenario state** | Select `normal-orchestration`, start scenario, advance to step 10 ("Reasoning budget") |
| **What should be visible** | Scenario catalog sidebar with six scenarios, scenario hero with progress counter, lifecycle steps with completed/current/pending states, decision explanation panel, affected resources, safety invariants, provenance detail, audit trail table |
| **Why it matters** | Shows the deterministic end-to-end scenario system—the primary interactive demonstration capability |
| **Recommended framing** | Full viewport; catalog, hero, lifecycle, and decision panels all visible |
| **Must-remain-visible labels** | SYNTHETIC provenance on each scenario card; "DETERMINISTIC DEMONSTRATION" header; scenario status chips; provenance badges in audit trail |
| **Portfolio / GitHub use** | Hero demo image, interactive capability showcase |

---

## Screenshot 11 — Governance & Evidence Audit

| Property | Value |
|---|---|
| **View** | `#/governance` then `#/evidence` (two captures, or one composite) |
| **Scenario state** | Default |
| **What should be visible** | **Governance:** Control decision pipeline flow, supervisory decisions table with HUMAN REVIEW/VERIFIED/UNKNOWN states, human control callout. **Evidence:** Decision ledger with full provenance chain, "not an external compliance attestation" callout |
| **Why it matters** | Shows UNKNOWN/DEFER/ESCALATE as first-class outcomes and complete traceability |
| **Recommended framing** | Full viewport each; or a side-by-side composite |
| **Must-remain-visible labels** | "UNKNOWN / DEFER / ESCALATE ARE FIRST-CLASS" eyebrow; HUMAN REVIEW chip; human control callout; provenance badges on every evidence row |
| **Portfolio / GitHub use** | Governance architecture, audit engineering |

---

## Screenshot 12 — Portfolio Page Hero

| Property | Value |
|---|---|
| **View** | Portfolio page (`ui/portfolio/index.html`) |
| **Scenario state** | N/A |
| **What should be visible** | Hero section with "Research / Experimental" chip, control loop orbit visualization, "Explore the Control Center" CTA, proof strip (31 phases, 1506 tests, 256 certification, 6 scenarios), "MEASURED + SYNTHETIC" provenance label, and boundary note |
| **Why it matters** | The external-facing portfolio presentation with integrated evidence and credibility boundary |
| **Recommended framing** | Full viewport from top; hero + proof strip visible |
| **Must-remain-visible labels** | "Research / Experimental" chip; "MEASURED + SYNTHETIC" provenance; boundary note; "Implements control-plane logic and deterministic demonstrations" text |
| **Portfolio / GitHub use** | Portfolio hero, social sharing, recruiter presentation |

---

## Capture priority

If time or context limits the number of captures, prioritize in this order:

1. Screenshot 01 — Mission Control Overview (hero image)
2. Screenshot 10 — Scenario Player (interactive demo capability)
3. Screenshot 05 — SLO Quality Conflict (safety differentiator)
4. Screenshot 04 — Compute Fabric & Topology (visual appeal)
5. Screenshot 06 — Migration & Recovery (resilience engineering)
6. Screenshot 12 — Portfolio Page Hero (external presentation)
7. Screenshot 03 — Execution Graph DAG (architecture)
8. Screenshot 07 — Scheduler Intelligence (adversarial design)
9. Remaining screenshots in listed order
