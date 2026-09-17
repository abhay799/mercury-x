import pytest

from mercury.disaggregated_execution.contracts import ExecutionHandoffKind
from mercury.disaggregated_execution.handoffs import create_execution_handoff
from mercury.disaggregated_execution.integration import (
    apply_prediction_hints,
    validate_context_handoff_reference,
    validate_kv_handoff_reference,
)
from mercury.global_memory.contracts import GlobalMemoryNamespace
from mercury.semantic_kv_cache.compatibility import evaluate_semantic_kv_compatibility
from mercury.semantic_kv_cache.contracts import SemanticKVLookupRequest
from tests._phase11_helpers import make_entry


def test_context_handoff_namespace_is_exact():
    handoff = create_execution_handoff(
        execution_plan_id="plan",
        namespace_type=GlobalMemoryNamespace.PROJECT,
        namespace_id="p1",
        producer_segment_id="a",
        consumer_segment_id="b",
        handoff_kind=ExecutionHandoffKind.CONTEXT,
        authorization_scope="project:p1",
        compatibility_contract_id="compat",
        verification_contract_id="verify",
        creation_sequence=1,
    )
    validate_context_handoff_reference(
        handoff,
        authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
        authorized_namespace_id="p1",
    )
    with pytest.raises(ValueError):
        validate_context_handoff_reference(
            handoff,
            authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
            authorized_namespace_id="p2",
        )


def test_kv_handoff_cannot_override_phase11():
    entry = make_entry()
    request = SemanticKVLookupRequest(
        namespace_type=GlobalMemoryNamespace.PROJECT,
        namespace_id="p1",
        authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
        authorized_namespace_id="p1",
        semantic_key="sem",
        semantic_fingerprint="fp",
        model_id="m",
        model_version="1",
        tokenizer_id="tok",
        attention_layout="gqa",
        kv_format="paged",
        precision="FP16",
        context_generation=1,
    )
    compat = evaluate_semantic_kv_compatibility(request, entry)
    handoff = create_execution_handoff(
        execution_plan_id="plan",
        namespace_type=GlobalMemoryNamespace.PROJECT,
        namespace_id="p1",
        producer_segment_id="a",
        consumer_segment_id="b",
        handoff_kind=ExecutionHandoffKind.KV_REFERENCE,
        authorization_scope="project:p1",
        compatibility_contract_id="phase11",
        verification_contract_id="verify",
        creation_sequence=1,
        payload_reference=entry.payload.payload_reference,
        payload_fingerprint=entry.payload.payload_fingerprint,
    )
    validate_kv_handoff_reference(handoff, entry, compat)
