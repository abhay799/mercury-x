from mercury.disaggregated_execution.contracts import (
    ExecutionHandoff,
    ExecutionHandoffKind,
    ExecutionHandoffState,
    make_handoff_id,
)


def create_execution_handoff(
    *,
    execution_plan_id,
    namespace_type,
    namespace_id,
    producer_segment_id,
    consumer_segment_id,
    handoff_kind: ExecutionHandoffKind,
    authorization_scope,
    compatibility_contract_id,
    verification_contract_id,
    creation_sequence,
    payload_reference=None,
    payload_fingerprint=None,
) -> ExecutionHandoff:
    handoff_id = make_handoff_id(
        execution_plan_id=execution_plan_id,
        producer_segment_id=producer_segment_id,
        consumer_segment_id=consumer_segment_id,
        handoff_kind=handoff_kind,
        creation_sequence=creation_sequence,
    )
    return ExecutionHandoff(
        handoff_id=handoff_id,
        execution_plan_id=execution_plan_id,
        namespace_type=namespace_type,
        namespace_id=namespace_id,
        producer_segment_id=producer_segment_id,
        consumer_segment_id=consumer_segment_id,
        handoff_kind=handoff_kind,
        payload_reference=payload_reference,
        payload_fingerprint=payload_fingerprint,
        authorization_scope=authorization_scope,
        compatibility_contract_id=compatibility_contract_id,
        verification_contract_id=verification_contract_id,
        state=ExecutionHandoffState.PENDING,
        creation_sequence=creation_sequence,
    )


def _replace(handoff: ExecutionHandoff, **updates) -> ExecutionHandoff:
    payload = handoff.model_dump()
    payload.update(updates)
    return ExecutionHandoff(**payload)


def make_handoff_available(handoff: ExecutionHandoff) -> ExecutionHandoff:
    if handoff.state is not ExecutionHandoffState.PENDING:
        raise ValueError("only PENDING handoff may become AVAILABLE")
    return _replace(handoff, state=ExecutionHandoffState.AVAILABLE)


def consume_handoff(handoff: ExecutionHandoff, *, consumer_segment_id: str) -> ExecutionHandoff:
    if handoff.state is not ExecutionHandoffState.AVAILABLE:
        raise ValueError("only AVAILABLE handoff may be consumed")
    if consumer_segment_id != handoff.consumer_segment_id:
        raise ValueError("handoff consumer mismatch")
    return _replace(handoff, state=ExecutionHandoffState.CONSUMED)


def invalidate_handoff(handoff: ExecutionHandoff, *, reason: str) -> ExecutionHandoff:
    if handoff.state not in (ExecutionHandoffState.PENDING, ExecutionHandoffState.AVAILABLE):
        raise ValueError("handoff state is terminal")
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("invalidation reason required")
    return _replace(
        handoff,
        state=ExecutionHandoffState.INVALIDATED,
        invalidation_reason=reason,
    )
