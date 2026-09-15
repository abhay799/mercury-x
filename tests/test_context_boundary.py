from __future__ import annotations

from pydantic import ValidationError
import pytest

from mercury.context.models import (
    ContextArtifact,
    ContextArtifactKind,
    ContextPortability,
    ContextReuseRequest,
    ContextStorageTier,
)
from mercury.context.reuse_gate import ContextReuseGate


INTEGRITY = "sha256:" + "a" * 64


def make_artifact(**overrides: object) -> ContextArtifact:
    values: dict[str, object] = {
        "artifact_id": "artifact-1",
        "owner_id": "owner-1",
        "tenant_id": "tenant-1",
        "authorized_owner_ids": ("owner-1",),
        "authorized_tenant_ids": ("tenant-1",),
        "kind": ContextArtifactKind.INPUT_CONTEXT,
        "portability": ContextPortability.PORTABLE,
        "storage_tier": ContextStorageTier.SYSTEM_RAM,
        "privacy_level": "confidential",
        "reference_uri": "mercury://context/artifact-1",
        "integrity_evidence": INTEGRITY,
    }
    values.update(overrides)
    return ContextArtifact(**values)


def make_request(**overrides: object) -> ContextReuseRequest:
    values: dict[str, object] = {
        "artifact_id": "artifact-1",
        "requester_owner_id": "owner-1",
        "requester_tenant_id": "tenant-1",
        "privacy_level": "confidential",
        "model_id": "model-1",
        "runtime_id": "runtime-1",
    }
    values.update(overrides)
    return ContextReuseRequest(**values)


def test_valid_portable_reuse_is_allowed():
    decision = ContextReuseGate().evaluate(make_artifact(), make_request())
    assert decision.allowed is True
    assert decision.reasons == ("reuse requirements satisfied",)


def test_unauthorized_or_privacy_incompatible_reuse_is_denied():
    artifact = make_artifact()
    owner_decision = ContextReuseGate().evaluate(
        artifact, make_request(requester_owner_id="owner-2")
    )
    privacy_decision = ContextReuseGate().evaluate(
        artifact, make_request(privacy_level="restricted")
    )
    assert "owner is not authorized" in owner_decision.reasons
    assert "privacy level is incompatible" in privacy_decision.reasons


def test_reuse_gate_fails_closed_for_integrity_and_portability_compatibility():
    request = make_request()
    assert ContextReuseGate().evaluate(
        make_artifact(integrity_evidence=None), request
    ).allowed is False
    assert ContextReuseGate().evaluate(
        make_artifact(
            portability=ContextPortability.MODEL_SPECIFIC, model_id="model-2"
        ), request
    ).allowed is False
    assert ContextReuseGate().evaluate(
        make_artifact(
            portability=ContextPortability.RUNTIME_SPECIFIC, runtime_id="runtime-2"
        ), request
    ).allowed is False


@pytest.mark.parametrize("forbidden_field", ["payload", "api_key", "token", "credentials"])
def test_artifacts_reject_payload_and_secret_fields(forbidden_field: str):
    with pytest.raises(ValidationError):
        make_artifact(**{forbidden_field: "forbidden"})


def test_contracts_are_immutable_and_tuple_backed():
    artifact = make_artifact()
    assert artifact.portability is ContextPortability.PORTABLE
    assert isinstance(artifact.authorized_owner_ids, tuple)
    with pytest.raises((AttributeError, TypeError, ValidationError)):
        artifact.authorized_owner_ids += ("owner-2",)


def test_every_decision_has_an_explicit_non_empty_reason():
    allowed = ContextReuseGate().evaluate(make_artifact(), make_request())
    denied = ContextReuseGate().evaluate(
        make_artifact(), make_request(artifact_id="other-artifact")
    )
    assert allowed.reasons and denied.reasons
