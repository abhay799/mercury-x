# MERCURY X — Phase 13 Hardware Personality Engine Hardening Addendum

## Scope
Close the remaining Phase 13 certification/design gaps before downstream phases consume hardware profiles.

## Locked hardening
- Certification gates must execute real invariants; unconditional placeholder PASS checks are forbidden.
- Phase 12 opaque requirement IDs remain opaque unless their semantics are certified.
- Workload affinity is evidence-first; insufficient evidence resolves to `UNKNOWN`.
- Measured profile values require matching verified `MEASURED` evidence and benchmark lineage.
- Declared and measured values remain independent.
- Deterministic CPU-first behavior is preserved.

## Completion
Phase 13 closes only after focused tests, executable certification, Phase 12 compatibility, full regression, and no known in-scope compromise.
