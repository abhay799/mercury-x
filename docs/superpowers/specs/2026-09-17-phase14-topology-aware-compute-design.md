# MERCURY X — Phase 14 Topology-Aware Compute Design

## Purpose
Model how certified compute resources are connected.

Phase 14 understands topology; it does not choose final placement.

## Boundary
- Phase 13: hardware capability.
- Phase 14: connectivity/topology.
- Phase 15: placement intelligence.

Phase 14 must not rank placements, schedule, migrate, provision, or select provider/region/model/precision.

## Core contracts
`TopologyNode`, `TopologyLink`, `TopologyGraph`.

Link kinds: `PCIE`, `NVLINK_LIKE`, `HIGH_SPEED_FABRIC`, `ETHERNET`, `INFINIBAND`, `SHARED_MEMORY`, `UNKNOWN`.

Locality domains: `DEVICE`, `HOST`, `RACK`, `ZONE`, `REGION`, `PROVIDER`, `UNKNOWN`.

Capability states: `AVAILABLE`, `UNAVAILABLE`, `UNKNOWN`.

Declared/measured bandwidth and latency remain separate. Missing evidence stays unknown. IDs/fingerprints are deterministic canonical SHA-256. Disconnected and cyclic physical graphs are valid.
