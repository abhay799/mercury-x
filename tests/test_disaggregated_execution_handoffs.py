import pytest

from mercury.disaggregated_execution.contracts import ExecutionHandoffKind, ExecutionHandoffState
from mercury.disaggregated_execution.handoffs import (
    consume_handoff,
    create_execution_handoff,
    invalidate_handoff,
    make_handoff_available,
)
from mercury.global_memory.contracts import GlobalMemoryNamespace


def handoff():
    return create_execution_handoff(
        execution_plan_id="plan",
        namespace_type=GlobalMemoryNamespace.PROJECT,
        namespace_id="p1",
        producer_segment_id="a",
        consumer_segment_id="b",
        handoff_kind=ExecutionHandoffKind.ARTIFACT,
        authorization_scope="project:p1",
        compatibility_contract_id="compat",
        verification_contract_id="verify",
        creation_sequence=1,
    )


def test_handoff_state_machine_and_consumer_authorization():
    pending = handoff()
    available = make_handoff_available(pending)
    assert available.state is ExecutionHandoffState.AVAILABLE
    consumed = consume_handoff(available, consumer_segment_id="b")
    assert consumed.state is ExecutionHandoffState.CONSUMED
    with pytest.raises(ValueError):
        consume_handoff(available, consumer_segment_id="x")


def test_invalidated_handoff_is_terminal():
    invalidated = invalidate_handoff(handoff(), reason="bad")
    assert invalidated.state is ExecutionHandoffState.INVALIDATED
    with pytest.raises(ValueError):
        make_handoff_available(invalidated)
