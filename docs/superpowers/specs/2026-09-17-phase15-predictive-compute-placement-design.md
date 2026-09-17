# MERCURY X — Phase 15 Predictive Compute Placement Design

## Purpose
Generate and rank eligible compute placement recommendations from Phase 12 requirements, Phase 13 hardware profiles, and Phase 14 topology evidence.

## Boundary
Phase 15 recommends placement; it does not execute, dispatch, reserve, provision, migrate, cancel, or mutate hardware/topology state.

## Baseline
Use a deterministic placement backend. No fake ML.

Allowed signals include explicit compatibility, memory headroom, precision/runtime support, topology locality/path capability, evidence quality, and uncertainty penalties.

Confidence bands: `LOW`, `MEDIUM`, `HIGH`.
Calibration states: `UNCALIBRATED`, `EMPIRICALLY_CALIBRATED`.
Baseline is `UNCALIBRATED`.

Equivalent inputs must produce identical candidate IDs, scores, ordering, prediction IDs, and reason codes.
