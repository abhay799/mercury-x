from __future__ import annotations

import pytest
from pydantic import ValidationError

from mercury.gateway.session import (
    IdempotencyKey,
    IdempotencyRecord,
    SessionIdentity,
    SessionRequestBinding,
    bind_gateway_session,
)


FINGERPRINT = "sha256:" + "a" * 64


def session(**overrides: object) -> SessionIdentity:
    values: dict[str, object] = {
        "session_id": "session-1",
        "owner_id": "owner-1",
        "tenant_id": "tenant-1",
    }
    values.update(overrides)
    return SessionIdentity(**values)


def bind(**overrides: object) -> SessionRequestBinding:
    values: dict[str, object] = {
        "binding_id": "binding-1",
        "session_identity": session(),
        "request_id": "request-1",
        "workload_id": "workload-1",
        "idempotency_key": IdempotencyKey(value="idempotency-1"),
        "request_fingerprint": FINGERPRINT,
        "existing_bindings": (),
    }
    values.update(overrides)
    return bind_gateway_session(**values)


def test_valid_session_binding():
    binding = bind()
    assert binding.session_identity.session_id == "session-1"


def test_valid_deterministic_idempotent_replay():
    original = bind()
    replay = bind(existing_bindings=(original,))
    assert replay is original


def test_blank_session_id_is_rejected():
    with pytest.raises(ValidationError):
        session(session_id=" ")


@pytest.mark.parametrize("field", ["owner_id", "tenant_id"])
def test_blank_owner_or_tenant_id_is_rejected(field: str):
    with pytest.raises(ValidationError):
        session(**{field: " "})


def test_blank_idempotency_key_is_rejected():
    with pytest.raises(ValidationError):
        IdempotencyKey(value=" ")


def test_same_key_with_different_fingerprint_is_rejected():
    original = bind()
    with pytest.raises(ValueError, match="fingerprint"):
        bind(request_fingerprint="sha256:" + "b" * 64, existing_bindings=(original,))


def test_owner_and_tenant_mutation_is_prevented():
    original = bind()
    with pytest.raises(ValueError, match="identity"):
        bind(
            session_identity=session(owner_id="owner-2"),
            existing_bindings=(original,),
        )


def test_workload_cannot_silently_rebind_to_another_session():
    original = bind()
    with pytest.raises(ValueError, match="session"):
        bind(
            session_identity=session(session_id="session-2"),
            existing_bindings=(original,),
        )


def test_session_and_idempotency_records_are_immutable():
    binding = bind()
    with pytest.raises((AttributeError, TypeError, ValidationError)):
        binding.idempotency_record.request_fingerprint = "sha256:" + "c" * 64


@pytest.mark.parametrize("field", ["payload", "token", "secret", "credentials"])
def test_raw_payload_and_secret_extra_fields_are_rejected(field: str):
    with pytest.raises(ValidationError):
        IdempotencyRecord(
            idempotency_key=IdempotencyKey(value="idempotency-1"),
            request_id="request-1",
            workload_id="workload-1",
            session_id="session-1",
            request_fingerprint=FINGERPRINT,
            **{field: "forbidden"},
        )


def test_request_workload_and_session_identity_is_preserved():
    binding = bind()
    assert binding.request_id == "request-1"
    assert binding.workload_id == "workload-1"
    assert binding.idempotency_record.session_id == "session-1"


def test_no_model_or_hardware_fields_are_exposed():
    fields = set(SessionRequestBinding.model_fields)
    assert not fields.intersection(
        {"selected_model_id", "model_selection", "selected_hardware_id", "hardware_selection"}
    )
