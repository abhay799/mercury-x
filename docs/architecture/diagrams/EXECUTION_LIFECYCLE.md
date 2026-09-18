# MERCURY X Execution Lifecycle

## Purpose

This diagram follows the canonical MERCURY X lifecycle and makes its fail-closed decision paths explicit. No branch permits silent quality degradation.

```mermaid
flowchart TD
    sense[Sense]
    understand[Understand Workload]
    graph[Build Execution Graph]
    model[Select compatible Model / Precision candidates]
    context[Resolve Context / Memory]
    hardware[Understand Hardware / Topology]
    place[Place Compute]
    budget[Allocate Reasoning Budget]
    slo[Enforce Quality / SLO]
    negotiate[Negotiate Compute]
    execute[Execute through an authorized runtime boundary]
    observe[Observe]
    resilient{Migration or healing needed?}
    migrate[Migrate / Heal]
    challenge[Challenge Decisions]
    simulate[Simulate Alternatives]
    learn[Learn Safely]
    govern[Govern]
    verify[Verify]
    next[Next authorized lifecycle generation]

    sense --> understand --> graph --> model --> context
    context --> hardware --> place --> budget --> slo --> negotiate
    negotiate --> execute --> observe --> resilient
    resilient -- yes --> migrate --> challenge
    resilient -- no --> challenge
    challenge --> simulate --> learn --> govern --> verify --> next
    next -. governed feedback .-> sense

    evidence{Evidence sufficient and consistent?}
    freshness{State generations current?}
    quality{Quality and hard SLO maintained?}
    unknown[UNKNOWN / DEFER / ESCALATE]
    recompute[REJECT stale decision and recompute]
    constrained[REJECT, COUNTEROFFER, or request additional resources]

    understand --> evidence
    evidence -- yes --> graph
    evidence -- no --> unknown
    place --> freshness
    freshness -- yes --> budget
    freshness -- no --> recompute
    slo --> quality
    quality -- yes --> negotiate
    quality -- no --> constrained
    unknown -. new evidence or authority .-> understand
    recompute -. refreshed generations .-> hardware
    constrained -. explicit revised resources or approved negotiation .-> slo
```

## Explanation

The main path advances only while typed evidence, authorization, freshness, and hard constraints remain valid. “Select” and “place” refer to logical control decisions supported by the relevant phase contracts. An UNKNOWN, stale, or infeasible state must leave the success path until new evidence, a recomputation, or an explicitly approved negotiation resolves it.

## Implementation and Runtime Boundary

MERCURY X implements the control logic surrounding this lifecycle. The “Execute” node marks an authorization boundary to a runtime; it does not claim that this repository contains a production cloud orchestrator, GPU runtime, or autonomous infrastructure operator.

