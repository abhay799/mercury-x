from dataclasses import FrozenInstanceError, fields
from datetime import UTC, datetime

import pytest

from mercury.contracts.workload_request import WorkloadRequest
from mercury.gateway.constraints import (
    ConstraintNormalizationResult,
    canonicalize_gateway_constraints,
)
from mercury.gateway.identity import GatewayIdentity
from mercury.gateway.models import (
    GatewayRequestEnvelope,
    GatewayValidationEvidence,
    GatewayValidationStatus,
)
from mercury.gateway.normalization import NormalizationResult, normalize_gateway_request
from mercury.intelligence.signals import WorkloadSignals, extract_workload_signals


def pipeline(**overrides: object) -> tuple[NormalizationResult, ConstraintNormalizationResult, WorkloadRequest]:
    values: dict[str, object] = {
        "workload_id": "workload-1",
        "session_id": "session-1",
        "task_type": "inference",
        "input": {"prompt_reference": "mercury://input/1"},
        "context": {},
        "latency_target_ms": 100.0,
        "quality_target": 0.9,
        "cost_budget": 2.5,
        "privacy_level": "confidential",
        "priority": 50,
        "hardware_constraints": (),
    }
    values.update(overrides)
    request = WorkloadRequest(**values)
    identity = GatewayIdentity(request_id="request-1", workload_id="workload-1", session_id="session-1")
    envelope = GatewayRequestEnvelope(
        gateway_request_id="gateway-request-1",
        identity=identity,
        workload_request=request,
        received_at=datetime(2026, 9, 16, tzinfo=UTC),
        normalized=False,
        validation_status=GatewayValidationStatus.ACCEPTED,
        validation_evidence=GatewayValidationEvidence(status=GatewayValidationStatus.ACCEPTED, reasons=()),
    )
    normalization = normalize_gateway_request(envelope)
    assert normalization.normalized_request is not None
    return normalization, canonicalize_gateway_constraints(identity, normalization.normalized_request), request


def signals(**overrides: object) -> WorkloadSignals:
    normalization, constraints, _ = pipeline(**overrides)
    return extract_workload_signals(normalization, constraints)


def test_minimal_normalized_request_extracts_deterministic_absent_signals() -> None:
    result = signals()

    assert result.explicit_modalities == ()
    assert result.text_input_present is None
    assert result.text_character_count is None
    assert result.output_type is None


def test_request_workload_and_session_identity_are_preserved_exactly() -> None:
    result = signals()

    assert (result.request_id, result.workload_id, result.session_id) == ("request-1", "workload-1", "session-1")


def test_explicit_text_input_is_detected_without_token_estimation() -> None:
    result = signals(input={"text": "hello"})

    assert result.text_input_present is True
    assert result.text_character_count == 5
    assert result.explicit_modalities == ("text",)


def test_explicit_multimodal_input_is_represented_by_exact_keys() -> None:
    result = signals(input={"text": "hi", "images": [{"id": "i-1"}], "audio": ["a-1"], "video": ["v-1"], "structured_data": {"key": "value"}})

    assert result.explicit_modalities == ("audio", "image", "structured_data", "text", "video")
    assert result.explicit_modality_count == 5
    assert result.attachment_count == 3


def test_input_size_metrics_are_deterministic_when_explicitly_represented() -> None:
    result = signals(input={"text": "hello", "items": [1, 2], "messages": ["a"], "segments": ["x", "y"]})

    assert (result.text_character_count, result.input_item_count, result.message_count, result.segment_count) == (5, 2, 1, 2)


def test_explicit_context_signals_are_extracted() -> None:
    result = signals(context={"conversation": ["prior"], "long_context": True, "references": ["ctx-b", "ctx-a", "ctx-a"]})

    assert result.explicit_context_supplied is True
    assert result.conversation_context_present is True
    assert result.long_context_requested is True
    assert result.context_references == ("ctx-a", "ctx-b")


def test_explicit_tool_requirement_is_extracted() -> None:
    result = signals(input={"tool_use": True, "tools": ["search", "calendar", "search"], "external_action_required": True})

    assert result.tool_use_requested is True
    assert result.declared_tool_names == ("calendar", "search")
    assert result.external_action_required is True


def test_canonical_latency_constraint_is_preserved_without_interpretation() -> None:
    result = signals()

    assert result.latency_constraint is not None
    assert (result.latency_constraint.value, result.latency_constraint.unit) == (100.0, "ms")


def test_canonical_quality_constraint_is_preserved_without_classification() -> None:
    assert signals().quality_constraint.value == 0.9  # type: ignore[union-attr]


def test_canonical_privacy_constraint_is_preserved_without_classification() -> None:
    assert signals().privacy_constraint.value == "confidential"  # type: ignore[union-attr]


def test_explicit_output_format_and_streaming_are_extracted() -> None:
    result = signals(input={"output_type": "json", "structured_output_required": True, "streaming": True})

    assert (result.output_type, result.structured_output_required, result.streaming_requested) == ("json", True, True)


def test_identical_input_produces_equal_signals() -> None:
    first = signals(input={"tools": ["search", "calendar"]})
    second = signals(input={"tools": ["calendar", "search"]})

    assert first == second


def test_signal_result_and_collections_are_immutable() -> None:
    result = signals(input={"tools": ["search"]})

    with pytest.raises(FrozenInstanceError):
        result.request_id = "changed"  # type: ignore[misc]
    assert isinstance(result.declared_tool_names, tuple)
    with pytest.raises(AttributeError):
        result.declared_tool_names.append("changed")  # type: ignore[attr-defined]


def test_blank_or_inconsistent_identity_fails_closed() -> None:
    normalization, constraints, _ = pipeline()
    blank_identity = normalization.model_copy(update={"request_id": " "})
    inconsistent_constraints = constraints.model_copy(update={"session_id": "other-session"})

    with pytest.raises(ValueError, match="identity"):
        extract_workload_signals(blank_identity, constraints)
    with pytest.raises(ValueError, match="identity"):
        extract_workload_signals(normalization, inconsistent_constraints)


def test_phase1_request_objects_are_not_mutated() -> None:
    normalization, constraints, request = pipeline(input={"text": "hello", "tools": ["search"]})
    before_request = request.model_dump(mode="python")
    before_normalization = normalization.model_dump(mode="python")
    before_constraints = constraints.model_dump(mode="python")

    extract_workload_signals(normalization, constraints)

    assert request.model_dump(mode="python") == before_request
    assert normalization.model_dump(mode="python") == before_normalization
    assert constraints.model_dump(mode="python") == before_constraints


def test_keyword_like_content_does_not_trigger_semantic_guessing() -> None:
    result = signals(input={"notes": "use image audio video and tools"}, task_type="general")

    assert result.explicit_modalities == ()
    assert result.tool_use_requested is None


def test_forbidden_model_hardware_placement_and_reasoning_fields_are_absent() -> None:
    forbidden = {"reasoning_complexity", "model_id", "provider", "hardware", "device", "gpu", "cpu", "region", "placement", "scheduler_decision", "execution_graph", "runtime_execution", "speculative_execution"}

    assert forbidden.isdisjoint({field.name for field in fields(WorkloadSignals)})
