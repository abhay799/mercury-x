# MERCURY X System Overview

## Purpose

This diagram presents MERCURY X as a logical AI compute control plane. It shows the primary flow from an authorized workload request through workload understanding, execution planning, control decisions, resilience, simulation, governance, and platform supervision.

```mermaid
flowchart TB
    request[Workload / Request]

    subgraph understand[Understand and Plan]
        gateway[Cognitive Gateway]
        intelligence[Workload Intelligence]
        graph[Execution Graph]
    end

    subgraph adapt[Adapt Models and Context]
        model[Model / Capability / Precision Intelligence]
        memory[Memory and Context Fabric]
    end

    subgraph decide[Understand Resources and Decide]
        hardware[Hardware / Topology / Placement Intelligence]
        reasoning[Reasoning / Quality / SLO Intelligence]
        negotiation[Compute Negotiation]
    end

    subgraph control[Control and Resilience]
        execution[Execution Control]
        resilience[Migration / Recovery]
    end

    subgraph govern[Challenge, Simulate, and Govern]
        challenge[Scheduler Challenge / Counterfactual Simulation]
        policy[Controlled Policy Evolution]
        federation[Federation / Privacy]
        twin[Datacenter Digital Twin]
        supervisory[Control Intelligence]
    end

    platform[MERCURY Platform]

    request --> gateway --> intelligence --> graph
    graph --> model --> memory --> hardware
    hardware --> reasoning --> negotiation --> execution
    execution --> resilience --> challenge --> policy
    policy --> federation --> twin --> supervisory --> platform
    platform -. telemetry and governed feedback .-> gateway

    subgraph safeguards[Cross-cutting control boundaries]
        authorization[Authorization]
        provenance[Provenance]
        quality[Quality and SLO invariants]
        privacy[Privacy and residency]
        stale[Stale-state protection]
        human[Human control / escalation]
        verification[Verification]
    end

    safeguards -. constrain and validate .-> understand
    safeguards -. constrain and validate .-> adapt
    safeguards -. constrain and validate .-> decide
    safeguards -. constrain and validate .-> control
    safeguards -. constrain and validate .-> govern
```

## Explanation

The main path is a control-artifact lifecycle, not a diagram of physically deployed microservices. Each domain preserves typed identities, evidence, constraints, generations, and provenance for the next decision boundary. Feedback is governed: observations may inform later requests or policy proposals, but they do not silently create authority or weaken hard requirements.

## Implementation and Runtime Boundary

The repository implements control-plane contracts, deterministic engines, validation, simulations, lifecycle logic, and internal certification gates. Distributed services, cloud control planes, accelerator runtimes, and real datacenter actuation remain optional infrastructure integrations and are not implied by this diagram.

