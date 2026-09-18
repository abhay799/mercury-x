# MERCURY X Short Demo Script

## Overview

| Property | Value |
|---|---|
| **Duration** | ~75 seconds (60–90 second range) |
| **Format** | Screen recording with narration or text overlay |
| **Audience** | Portfolio visitors, LinkedIn/project posts, recruiter introductions |
| **Tone** | Concise, confident, technically honest |
| **Surfaces** | Portfolio page hero, Control Center (3 views) |

The short demo communicates: **problem → architecture → strongest capabilities → evidence → boundary.**

---

## Segment 1 — Problem + Identity (0:00–0:12)

| Property | Value |
|---|---|
| **Screen** | Portfolio page hero section |
| **User action** | Page loads; no interaction |
| **Narration** | "AI execution is a coupled control problem. Model capability, compute, quality, context, topology, privacy, failures, and policy all constrain the same decision. MERCURY X is a control-plane architecture that coordinates them without turning missing evidence into permission." |
| **Important visual** | Hero copy; orbit visualization; "Research / Experimental" chip |
| **Duration** | 12 seconds |

---

## Segment 2 — Architecture Scope (0:12–0:22)

| Property | Value |
|---|---|
| **Screen** | Portfolio page proof strip + architecture section |
| **User action** | Brief scroll to proof strip and architecture grid |
| **Narration** | "Thirty-one phases across nine layers—from workload intelligence and model adaptation through memory, placement, reasoning, migration, scheduling, federation, and supervisory control. Over 1500 local tests and six deterministic demo scenarios." |
| **Important visual** | Proof strip numbers (31, 1506, 256, 6); layer cards; "MEASURED + SYNTHETIC" provenance label |
| **Duration** | 10 seconds |

---

## Segment 3 — Mission Control + Quality Safety (0:22–0:42)

| Property | Value |
|---|---|
| **Screen** | Control Center overview → SLO view with quality conflict scenario |
| **User action** | Open Control Center; brief overview pause; then show `#/slo` with the quality-slo-conflict scenario at step 4 |
| **Narration** | "The Control Center is provenance-first—every artifact declares whether it's synthetic, simulated, or static demonstration. When resource pressure threatens quality, MERCURY rejects silent degradation and issues an explicit counteroffer. Quality, verification, and safety floors are protected and cannot be weakened automatically." |
| **Important visual** | Mode banner; source legend; scenario conflict callout; "NO SILENT QUALITY DEGRADATION" with ENFORCED chips |
| **Duration** | 20 seconds |

---

## Segment 4 — Migration Authority (0:42–0:55)

| Property | Value |
|---|---|
| **Screen** | Migration & Recovery view with live-migration scenario at step 8 |
| **User action** | Navigate to `#/migration` |
| **Narration** | "Logical workload migration preserves exactly one authoritative executor with verified cutover and armed rollback. This is simulated control-plane state—not physical GPU memory transfer. The claim boundary is always visible." |
| **Important visual** | Migration timeline; authority lock; SIMULATED provenance badges |
| **Duration** | 13 seconds |

---

## Segment 5 — Evidence + Boundary (0:55–1:15)

| Property | Value |
|---|---|
| **Screen** | System Status view (`#/system`) |
| **User action** | Navigate to `#/system` |
| **Narration** | "The claim matrix states what is implemented, what is simulated, and what is explicitly not claimed. Control-plane logic: implemented. Production infrastructure: not connected. GPU live migration: not claimed. Autonomous policy promotion: forbidden. MERCURY X is a research-oriented, CPU-first control-plane architecture. Claims stop where evidence stops." |
| **Important visual** | Claim matrix with colored chips (IMPLEMENTED / NOT CONNECTED / NOT CLAIMED / FORBIDDEN) |
| **Duration** | 20 seconds |

---

## Production notes

- **Word count:** ~210 words at ~170 words/minute = ~75 seconds.
- **Pacing:** Each transition should have a 1-second visual pause. Do not rush.
- **Text overlay option:** If narration is impractical, use text overlays synced to the key phrases above. Use a clean sans-serif typeface on a semi-transparent dark background.
- **Music option:** If adding background music, keep it minimal and low in the mix. Do not use music that implies enterprise scale or production deployment.
- **Editing:** Record at natural pace (~2 minutes), then tighten transitions in editing. Do not cut provenance labels or boundary callouts.
- **Thumbnail:** Use Screenshot 01 (Mission Control Overview) or Screenshot 12 (Portfolio Hero) as the thumbnail.

## Claim-safety checklist

Before publishing, verify the final recording does not:

- [ ] Imply production deployment
- [ ] Hide provenance or claim-boundary labels
- [ ] Present synthetic data as live telemetry
- [ ] Claim physical GPU migration
- [ ] Present test counts as performance metrics
