# MERCURY X Migration and Recovery

## Purpose

This diagram focuses on Phase 21 migration and Phase 22 self-healing. It shows verified control-plane state transfer, exactly-one-authoritative-executor cutover, rollback, and post-recovery verification.

```mermaid
flowchart TD
    subgraph P21[Phase 21 — Live AI Workload Migration]
        nodeA[Running workload on Node A]
        trigger[Migration trigger with evidence]
        eligible{Eligibility and current generations valid?}
        destination[Certified destination candidate]
        capture[Capture MERCURY execution-state checkpoint]
        transfer[Transfer checkpoint and context references]
        restore[Restore candidate execution on Node B]
        equivalent{Verify destination equivalence?}
        cutover[Atomic exactly-one-authoritative-executor cutover]
        retire[Retire Node A authority]
        rollback[Rollback]
        safe[Restore safe authoritative source state]
        migrationEscalate[Fail / defer / escalate]

        nodeA --> trigger --> eligible
        eligible -- yes --> destination --> capture --> transfer --> restore --> equivalent
        eligible -- no / stale --> migrationEscalate
        equivalent -- yes --> cutover --> retire
        equivalent -- no --> rollback --> safe
        cutover -- conflict or failure --> rollback
    end

    subgraph preserved[Conceptually preserved and validated state]
        identity[Model and version / precision]
        graph[Graph position]
        context[Session context / KV and cache references where represented]
        verification[Verification state]
        reasoning[Reasoning budget and progress]
        placement[Placement provenance / topology generation]
        slo[SLO / intelligence contract]
        scheduler[Scheduler ownership]
        speculation[Speculation state]
        security[Authorization and security context]
        generation[Migration generation and fingerprint]
    end

    preserved -. sealed into and checked against .-> capture
    preserved -. equivalence checks .-> equivalent

    subgraph P22[Phase 22 — Self-Healing AI Infrastructure]
        detect[Detect failure or degradation]
        diagnose[Diagnose and build bounded recovery candidates]
        decision{Safe recovery decision exists?}
        recovery[Apply authorized recovery action]
        verify{Post-recovery verification passes?}
        resume[Resume from verified authoritative state]
        healingEscalate[Fail / defer / escalate]

        detect --> diagnose --> decision
        decision -- yes --> recovery --> verify
        decision -- no --> healingEscalate
        verify -- yes --> resume
        verify -- no --> healingEscalate
    end

    migrationEscalate --> detect
    safe --> detect
    retire -. later degradation .-> detect
```

## Explanation

Migration begins from explicit trigger evidence and checks eligibility, topology, placement, scheduler, agreement, authorization, and execution generations. The checkpoint represents MERCURY control state and context references. Restore is provisional until equivalence verification succeeds. Cutover makes one executor authoritative; a verification or cutover failure follows the rollback path.

Self-healing consumes a detected failure and selects only candidates that preserve hard constraints such as quality, authorization, and privacy. Recovery is not complete until post-action verification succeeds.

## Implementation and Runtime Boundary

The repository implements migration/healing contracts, eligibility and safety checks, state transitions, ledger behavior, rollback logic, and verification boundaries. “Transfer” and “restore” describe control-plane artifacts and references. This is not a claim of OS, VM, container, device-memory, or live GPU-memory migration across production hosts.

