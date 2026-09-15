from __future__ import annotations

import pytest
from pydantic import ValidationError

from mercury.runtime.trace_context import (
    ExecutionIdentity,
    TraceContext,
    TraceLink,
    TraceRelation,
)


def identity(**overrides: object) -> ExecutionIdentity:
    values: dict[str, object] = {
        "request_id": "request-1",
        "workload_id": "workload-1",
        "execution_id": "execution-1",
    }
    values.update(overrides)
    return ExecutionIdentity(**values)


def context(**overrides: object) -> TraceContext:
    values: dict[str, object] = {
        "trace_id": "trace-1",
        "span_id": "span-1",
        "parent_span_id": None,
        "identity": identity(),
        "node_id": "node-1",
        "attempt": 0,
    }
    values.update(overrides)
    return TraceContext(**values)


def link(**overrides: object) -> TraceLink:
    values: dict[str, object] = {
        "link_id": "link-1",
        "relation": TraceRelation.RETRY_OF,
        "source_trace_id": "trace-1",
        "source_span_id": "span-1",
        "target_trace_id": "trace-1",
        "target_span_id": "span-0",
    }
    values.update(overrides)
    return TraceLink(**values)


def test_valid_execution_identity():
    assert identity().execution_id == "execution-1"


@pytest.mark.parametrize("field", ["request_id", "workload_id", "execution_id"])
def test_blank_execution_identity_ids_are_rejected(field: str):
    with pytest.raises(ValidationError):
        identity(**{field: " "})


def test_valid_trace_context():
    assert context().trace_id == "trace-1"


@pytest.mark.parametrize("field", ["trace_id", "span_id", "node_id"])
def test_blank_trace_span_or_node_ids_are_rejected(field: str):
    with pytest.raises(ValidationError):
        context(**{field: " "})


def test_negative_attempt_is_rejected():
    with pytest.raises(ValidationError):
        context(attempt=-1)


def test_span_cannot_be_its_own_parent():
    with pytest.raises(ValidationError):
        context(parent_span_id="span-1")


def test_trace_link_cannot_point_a_span_to_itself():
    with pytest.raises(ValidationError):
        link(target_span_id="span-1")


@pytest.mark.parametrize(
    "relation", [TraceRelation.RETRY_OF, TraceRelation.FALLBACK_FROM, TraceRelation.MIGRATED_FROM]
)
def test_explicit_retry_fallback_and_migration_relation_is_preserved(relation: TraceRelation):
    assert link(relation=relation).relation is relation


def test_models_and_containers_remain_immutable():
    trace = context()
    with pytest.raises((AttributeError, TypeError, ValidationError)):
        trace.identity.request_id = "request-2"


@pytest.mark.parametrize("field", ["payload", "api_key", "token", "credentials"])
def test_extra_payload_and_secret_fields_are_rejected(field: str):
    with pytest.raises(ValidationError):
        context(**{field: "forbidden"})


def test_execution_identity_remains_unchanged_when_attached_to_trace_context():
    execution_identity = identity()
    trace = context(identity=execution_identity)
    assert trace.identity == execution_identity
