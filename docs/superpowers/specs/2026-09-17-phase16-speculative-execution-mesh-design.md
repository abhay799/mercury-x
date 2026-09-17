# MERCURY X — Phase 16 Speculative Execution Mesh Design

## Purpose
Represent bounded speculative execution over certified Phase 15 candidates without uncontrolled duplication.

## Fundamental rule
No speculative result becomes authoritative until verification passes and the commit policy selects it.

Branch states: `PLANNED`, `READY`, `RUNNING`, `SUCCEEDED`, `FAILED`, `CANCELLED`, `COMMITTED`, `DISCARDED`.

Speculation has explicit bounded fan-out, no recursive speculation, no hidden retries, deterministic winner selection, auditable cancellation/discard, and exactly one authoritative committed result.

Phase 16 may not widen authorization, bypass Phase 12 readiness, override Phase 13 compatibility, override Phase 14 topology constraints, recompute Phase 15 placement scores, bypass verification, or perform migration.
