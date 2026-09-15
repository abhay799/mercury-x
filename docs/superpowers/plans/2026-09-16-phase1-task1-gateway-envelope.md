# Phase 1 Task 1: Gateway Request Envelope and Identity Baseline

Implement immutable gateway identity, validation evidence, and request-envelope contracts around the certified `WorkloadRequest`.

## Scope

- Preserve the original `WorkloadRequest` instance and values.
- Require explicit gateway identity, receipt time, normalization state, and validation outcome.
- Fail closed for blank identities, inconsistent validation evidence, identity mismatches, and secret-bearing extra fields.

## Non-goals

No Workload Intelligence, model or hardware selection, scheduling, execution, or later Phase 1 work.
