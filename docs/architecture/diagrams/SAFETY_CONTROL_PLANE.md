# MERCURY X Safety Control Plane

## Purpose

This diagram shows how hard safety invariants surround an action. A failed hard gate cannot fall through to execution.

```mermaid
flowchart TD
    request[Request]
    authority{Policy and authority valid?}
    evidence{Evidence and provenance complete?}
    freshness{Versions and generations current?}
    quality{Quality, verification, and SLO constraints hold?}
    privacy{Privacy, purpose, and residency hold?}
    simulation{Production action rather than advisory simulation?}
    approval{Required human approval present and exact?}
    authorization[Execution authorization]
    action[Action through runtime boundary]
    post{Post-action verification passes?}
    complete[Verified control outcome]

    request --> authority
    authority -- yes --> evidence
    evidence -- yes --> freshness
    freshness -- yes --> quality
    quality -- yes --> privacy
    privacy -- yes --> simulation
    simulation -- yes --> approval
    approval -- yes / not required --> authorization --> action --> post
    post -- yes --> complete

    reject[REJECT / FAIL]
    defer[DEFER / UNKNOWN]
    stale[REJECT and recompute]
    escalate[ESCALATE / explicit counteroffer]
    advisory[ADVISORY ONLY<br/>no production side effect]
    recover[Rollback / safe recovery / escalation]

    authority -- no --> reject
    evidence -- no or unknown --> defer
    freshness -- no --> stale
    quality -- no --> escalate
    privacy -- no --> reject
    simulation -- no --> advisory
    approval -- missing or mismatched --> reject
    post -- no --> recover

    subgraph invariants[Cross-cutting hard invariants]
        q[QUALITY]
        a[AUTHORIZATION]
        p[PRIVACY]
        s[STALE STATE]
        sim[SIMULATION IS NOT EXECUTION]
        pe[CONTROLLED POLICY EVOLUTION]
        m[MIGRATION AUTHORITY]
        r[RECOVERY VERIFICATION]
        u[UNKNOWN IS NOT APPROVAL]
        h[HUMAN CONTROL]
    end

    invariants -. constrain every gate .-> request
    invariants -. constrain every gate .-> authorization
    invariants -. constrain every gate .-> post
```

## Explanation

The pipeline distinguishes hard rejection from temporary deferral and human escalation. Quality cannot be silently lowered to make a request fit. Simulation cannot cross into action. Migration and recovery remain constrained by the original authority and require verification. Policy evolution is evaluated in controlled states and cannot autonomously promote itself into production.

## Implementation and Runtime Boundary

The safety control plane is represented by repository contracts, validators, lifecycle engines, tests, and internal certification gates. It is not a claim of external regulatory certification, a complete production threat model, or hardware-backed enforcement.

