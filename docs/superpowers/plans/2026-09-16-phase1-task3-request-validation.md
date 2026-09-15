# Phase 1 Task 3: Gateway Request Validation Baseline

Implement immutable gateway validation evidence around the certified `WorkloadRequest`.

## Scope

- Validate raw gateway identity and workload-request representations without rewriting them.
- Preserve valid request instances and request, workload, and session identity.
- Return explicit error evidence for missing identity, malformed requests, forbidden fields, and identity mismatches.

## Non-goals

No Workload Intelligence, model or hardware selection, scheduling, execution, or later Phase 1 work.
