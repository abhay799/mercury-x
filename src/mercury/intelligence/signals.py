"""Deterministic extraction of explicit workload signals from Phase 1 contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from mercury.gateway.constraints import (
    CanonicalConstraint,
    ConstraintKind,
    ConstraintNormalizationResult,
)
from mercury.gateway.normalization import NormalizationResult


_MODALITY_KEYS = {
    "text": "text",
    "image": "image",
    "images": "image",
    "audio": "audio",
    "video": "video",
    "structured_data": "structured_data",
    "code": "code",
}
_CONSTRAINT_KINDS = {
    ConstraintKind.LATENCY,
    ConstraintKind.QUALITY,
    ConstraintKind.PRIVACY,
    ConstraintKind.COST,
}


def _nonblank(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be nonblank")
    return value


def _string_values(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        candidates: Iterable[Any] = (value,)
    elif isinstance(value, (list, tuple, set, frozenset)):
        candidates = value
    else:
        return ()
    return tuple(sorted({item.strip() for item in candidates if isinstance(item, str) and item.strip()}))


def _count_items(value: Any) -> int | None:
    if isinstance(value, (list, tuple, set, frozenset, dict)):
        return len(value)
    return None


def _explicit_bool(mapping: dict[str, Any], key: str) -> bool | None:
    value = mapping.get(key)
    return value if key in mapping and isinstance(value, bool) else None


@dataclass(frozen=True)
class SignalEvidence:
    signal_group: str
    source_fields: tuple[str, ...]

    def __post_init__(self) -> None:
        _nonblank(self.signal_group, "signal_group")
        sources = _string_values(self.source_fields)
        if not sources:
            raise ValueError("source_fields must not be empty")
        object.__setattr__(self, "source_fields", sources)


@dataclass(frozen=True)
class WorkloadSignals:
    request_id: str
    workload_id: str
    session_id: str
    text_input_present: bool | None
    image_input_present: bool | None
    audio_input_present: bool | None
    video_input_present: bool | None
    structured_data_present: bool | None
    code_input_present: bool | None
    explicit_modalities: tuple[str, ...]
    explicit_modality_count: int
    text_character_count: int | None
    input_item_count: int | None
    message_count: int | None
    segment_count: int | None
    attachment_count: int | None
    explicit_context_supplied: bool | None
    conversation_context_present: bool | None
    long_context_requested: bool | None
    context_references: tuple[str, ...]
    tool_use_requested: bool | None
    declared_tool_names: tuple[str, ...]
    external_action_required: bool | None
    latency_constraint: CanonicalConstraint | None
    quality_constraint: CanonicalConstraint | None
    privacy_constraint: CanonicalConstraint | None
    cost_constraint: CanonicalConstraint | None
    output_type: str | None
    structured_output_required: bool | None
    streaming_requested: bool | None
    evidence: tuple[SignalEvidence, ...]

    def __post_init__(self) -> None:
        for name in ("request_id", "workload_id", "session_id"):
            _nonblank(getattr(self, name), name)
        object.__setattr__(self, "explicit_modalities", _string_values(self.explicit_modalities))
        object.__setattr__(self, "context_references", _string_values(self.context_references))
        object.__setattr__(self, "declared_tool_names", _string_values(self.declared_tool_names))
        evidence = tuple(sorted(set(self.evidence), key=lambda item: (item.signal_group, item.source_fields)))
        if not evidence:
            raise ValueError("evidence must not be empty")
        object.__setattr__(self, "evidence", evidence)


def _constraint_by_kind(
    constraints: tuple[CanonicalConstraint, ...], kind: ConstraintKind
) -> CanonicalConstraint | None:
    matches = tuple(item for item in constraints if item.kind is kind)
    if len(matches) > 1:
        raise ValueError(f"canonical {kind.value} constraint is ambiguous")
    return matches[0] if matches else None


def extract_workload_signals(
    normalization: NormalizationResult,
    constraints: ConstraintNormalizationResult,
) -> WorkloadSignals:
    """Extract only explicitly represented request signals and canonical constraints."""
    if not normalization.normalized or normalization.normalized_request is None:
        raise ValueError("normalization must be complete")
    if not constraints.canonicalized:
        raise ValueError("canonical constraints must be complete")
    identity = (normalization.request_id, normalization.workload_id, normalization.session_id)
    if any(not isinstance(value, str) or not value.strip() for value in identity):
        raise ValueError("normalization identity must be nonblank")
    if (constraints.request_id, constraints.workload_id, constraints.session_id) != identity:
        raise ValueError("constraint identity does not match normalized request identity")

    request = normalization.normalized_request
    input_data = request.input
    context_data = request.context
    modalities = {
        modality
        for key, modality in _MODALITY_KEYS.items()
        if key in input_data and input_data[key] is not None
    }
    if request.task_type == "code":
        modalities.add("code")
    explicit_modalities = tuple(sorted(modalities))

    def modality_presence(modality: str) -> bool | None:
        keys = tuple(key for key, name in _MODALITY_KEYS.items() if name == modality)
        if modality == "code" and request.task_type == "code":
            return True
        if not any(key in input_data for key in keys):
            return None
        return any(input_data.get(key) is not None for key in keys)

    text_value = input_data.get("text")
    text_character_count = len(text_value) if isinstance(text_value, str) else None
    attachment_count_values = [
        _count_items(input_data[key])
        for key in ("image", "images", "audio", "video")
        if key in input_data
    ]
    attachment_count = (
        sum(value for value in attachment_count_values if value is not None)
        if attachment_count_values and all(value is not None for value in attachment_count_values)
        else None
    )

    context_references = _string_values(
        context_data.get("references", context_data.get("retrieval_references", ()))
    )
    declared_tools = _string_values(input_data.get("tools", ()))
    declared_capabilities = _string_values(input_data.get("capabilities", ()))
    declared_tool_names = tuple(sorted(set((*declared_tools, *declared_capabilities))))
    output_type = input_data.get("output_type")
    output_type = output_type.strip() if isinstance(output_type, str) and output_type.strip() else None
    canonical_constraints = tuple(
        item for item in constraints.constraints if item.kind in _CONSTRAINT_KINDS
    )

    evidence = [SignalEvidence("identity", ("normalization.request_id", "normalization.workload_id", "normalization.session_id"))]
    if explicit_modalities:
        evidence.append(SignalEvidence("content", tuple(f"input.{key}" for key in _MODALITY_KEYS if key in input_data) + (("request.task_type",) if request.task_type == "code" else ())))
    if any(value is not None for value in (text_character_count, _count_items(input_data.get("items")), _count_items(input_data.get("messages")), _count_items(input_data.get("segments")), attachment_count)):
        evidence.append(SignalEvidence("input_size", tuple(f"input.{key}" for key in ("text", "items", "messages", "segments", "image", "images", "audio", "video") if key in input_data)))
    if context_data:
        evidence.append(SignalEvidence("context", tuple(f"context.{key}" for key in context_data)))
    if any(value is not None for value in (_explicit_bool(input_data, "tool_use"), _explicit_bool(input_data, "external_action_required"))) or declared_tool_names:
        evidence.append(SignalEvidence("tools", tuple(f"input.{key}" for key in ("tool_use", "tools", "capabilities", "external_action_required") if key in input_data)))
    if canonical_constraints:
        evidence.append(SignalEvidence("constraints", tuple(item.source_field for item in canonical_constraints)))
    if output_type is not None or any(_explicit_bool(input_data, key) is not None for key in ("structured_output_required", "streaming")):
        evidence.append(SignalEvidence("output", tuple(f"input.{key}" for key in ("output_type", "structured_output_required", "streaming") if key in input_data)))

    return WorkloadSignals(
        request_id=identity[0], workload_id=identity[1], session_id=identity[2],
        text_input_present=modality_presence("text"), image_input_present=modality_presence("image"),
        audio_input_present=modality_presence("audio"), video_input_present=modality_presence("video"),
        structured_data_present=modality_presence("structured_data"), code_input_present=modality_presence("code"),
        explicit_modalities=explicit_modalities, explicit_modality_count=len(explicit_modalities),
        text_character_count=text_character_count, input_item_count=_count_items(input_data.get("items")),
        message_count=_count_items(input_data.get("messages")), segment_count=_count_items(input_data.get("segments")),
        attachment_count=attachment_count, explicit_context_supplied=bool(context_data) if context_data else None,
        conversation_context_present=(bool(context_data.get("conversation")) if "conversation" in context_data else None),
        long_context_requested=_explicit_bool(context_data, "long_context"), context_references=context_references,
        tool_use_requested=_explicit_bool(input_data, "tool_use"), declared_tool_names=declared_tool_names,
        external_action_required=_explicit_bool(input_data, "external_action_required"),
        latency_constraint=_constraint_by_kind(canonical_constraints, ConstraintKind.LATENCY),
        quality_constraint=_constraint_by_kind(canonical_constraints, ConstraintKind.QUALITY),
        privacy_constraint=_constraint_by_kind(canonical_constraints, ConstraintKind.PRIVACY),
        cost_constraint=_constraint_by_kind(canonical_constraints, ConstraintKind.COST), output_type=output_type,
        structured_output_required=_explicit_bool(input_data, "structured_output_required"),
        streaming_requested=_explicit_bool(input_data, "streaming"), evidence=tuple(evidence),
    )
