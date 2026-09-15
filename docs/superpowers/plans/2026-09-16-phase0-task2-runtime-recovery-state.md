# Phase 0 Task 2: Runtime Recovery State Baseline

Implement immutable, evidence-only runtime recovery state contracts.

## Scope

- `RuntimeNodeStatus`, `FailureCategory`, and `RecoveryAction` enums.
- Immutable retry, failure, checkpoint, and execution recovery state records.
- Fail-closed validation for node-state overlap, identity, retry attempts, checkpoint uniqueness, and immutable tuple containers.

## Non-goals

No retry execution, scheduling, workers, migration, fallback automation, self-healing, GPU/cloud runtime, or later-phase work.
