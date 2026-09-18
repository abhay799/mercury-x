import pytest

from mercury.federated_execution.contracts import (
    DomainClass,
    FederationCapability,
    FederationIdentity,
    FederatedPlacementDecision,
    FederatedTopologySnapshot,
    validate_federation_generation,
    validate_federated_placement,
)
from mercury.federated_execution.engine import FederatedExecutionEngine


def test_federated_placement_preserves_residency_and_auth():
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
        residency_ok=True,
        auth_preserved=True,
        quality_preserved=True,
    )
    assert decision.decision_id.startswith("fed-placement:")
    assert validate_federated_placement(decision)

    bad = decision.model_copy(update={"residency_ok": False})
    assert not validate_federated_placement(bad)


def test_federated_generation_staleness_fails_closed():
    ok, reason = validate_federation_generation(current_generation=4, expected_generation=4)
    stale, stale_reason = validate_federation_generation(current_generation=3, expected_generation=4)
    assert ok and reason == "GENERATION_CURRENT"
    assert not stale and "STALE" in stale_reason
