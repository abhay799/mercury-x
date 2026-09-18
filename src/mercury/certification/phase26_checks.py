from mercury.federated_execution.contracts import (
    DomainClass,
    FederationCapability,
    FederationIdentity,
    FederatedTopologySnapshot,
)
from mercury.federated_execution.engine import FederatedExecutionEngine


def federated_placement():
    identity = FederationIdentity(
        identity_id="fed-1",
        domain_id="edge-a",
        domain_class=DomainClass.EDGE,
        generation=3,
        authorization_context_id="auth-edge",
        authorization_generation=2,
        provenance_ids=("p1",),
    )
    capability = FederationCapability(
        capability_id="cap-1",
        domain_id="cloud-b",
        domain_class=DomainClass.CLOUD,
        generation=3,
        residency_allowed=True,
        supports_model=True,
        supports_precision=True,
        capacity_available=True,
        latency_ms=25,
        quality_preserving=True,
        authorization_context_id="auth-edge",
        authorization_generation=2,
        provenance_ids=("p2",),
    )
    snapshot = FederatedTopologySnapshot(
        snapshot_id="snap-1",
        generation=3,
        domain_id="edge-a",
        regions=("region-1",),
        edges=("edge-a",),
        cloud_nodes=("cloud-b",),
        provenance_ids=("p3",),
    )
    decision = FederatedExecutionEngine().plan(
        identity,
        capability,
        snapshot,
        workload_id="job-1",
        destination_domain_id="cloud-b",
        destination_domain_class=DomainClass.CLOUD,
        residency_ok=True,
        auth_preserved=True,
        quality_preserved=True,
        generation=3,
        provenance_ids=("p4",),
    )
    return decision.residency_ok and decision.auth_preserved and decision.quality_preserved, "federated placement preserves residency, auth, and quality"


CHECKS = {"federated_placement": federated_placement}
