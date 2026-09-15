# Phase 1 Task 4: Gateway Session Identity and Idempotency Baseline

Implement immutable session identity, request binding, and idempotency evidence.

## Scope

- Bind request and workload identities to stable owner, tenant, and session evidence.
- Return the existing binding for deterministic replay of the same key and fingerprint.
- Reject fingerprint conflicts, owner or tenant mutation, and cross-session workload rebinding.
- Store fingerprints only; no raw request payload.

## Non-goals

No Workload Intelligence, model or hardware selection, scheduling, execution, or later Phase 1 work.
