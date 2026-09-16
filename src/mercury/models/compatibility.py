"""Deterministic hard-constraint compatibility evaluation for model capabilities."""

from __future__ import annotations

from enum import Enum
from typing import Iterable, TypeVar

from pydantic import field_validator

from mercury.contracts.base import ContractModel
from mercury.models.capabilities import (
    CapabilityStatus,
    ModelCapabilityRecord,
    ModelModality,
    ReasoningCapability,
)


class CompatibilityStatus(str, Enum):
    COMPATIBLE = "compatible"
    INCOMPATIBLE = "incompatible"


_EnumValue = TypeVar("_EnumValue", bound=Enum)


def _normalized_enum_tuple(
    values: Iterable[_EnumValue], enum_type: type[_EnumValue], field_name: str
) -> tuple[_EnumValue, ...]:
    normalized = tuple(sorted(set(values), key=lambda item: item.value))
    if any(not isinstance(item, enum_type) for item in normalized):
        raise ValueError(f"{field_name} must contain {enum_type.__name__} values")
    return normalized


class ModelCapabilityRequirements(ContractModel):
    """Explicit logical requirements for one model capability record."""

    required_input_modalities: tuple[ModelModality, ...] = ()
    required_output_modalities: tuple[ModelModality, ...] = ()
    required_reasoning_capabilities: tuple[ReasoningCapability, ...] = ()
    requires_tool_use: bool = False
    requires_retrieval: bool = False
    requires_code_generation: bool = False
    requires_code_understanding: bool = False
    requires_structured_tool_arguments: bool = False
    requires_tool_result_consumption: bool = False
    requires_json_output: bool = False
    requires_schema_constrained_output: bool = False
    minimum_context_tokens: int | None = None
    minimum_output_tokens: int | None = None
    requires_streaming: bool = False
    allowed_statuses: tuple[CapabilityStatus, ...] | None = None
    evidence: tuple[str, ...]

    @field_validator("required_input_modalities", "required_output_modalities", mode="after")
    @classmethod
    def normalize_modalities(
        cls, values: tuple[ModelModality, ...]
    ) -> tuple[ModelModality, ...]:
        return _normalized_enum_tuple(values, ModelModality, "required_modalities")

    @field_validator("required_reasoning_capabilities", mode="after")
    @classmethod
    def normalize_reasoning(
        cls, values: tuple[ReasoningCapability, ...]
    ) -> tuple[ReasoningCapability, ...]:
        return _normalized_enum_tuple(
            values, ReasoningCapability, "required_reasoning_capabilities"
        )

    @field_validator("allowed_statuses", mode="after")
    @classmethod
    def normalize_statuses(
        cls, values: tuple[CapabilityStatus, ...] | None
    ) -> tuple[CapabilityStatus, ...] | None:
        if values is None:
            return None
        normalized = _normalized_enum_tuple(values, CapabilityStatus, "allowed_statuses")
        if not normalized:
            raise ValueError("allowed_statuses must not be empty when declared")
        return normalized

    @field_validator("minimum_context_tokens", "minimum_output_tokens")
    @classmethod
    def minimums_are_positive(cls, value: int | None) -> int | None:
        if value is not None and (isinstance(value, bool) or value <= 0):
            raise ValueError("minimum token requirements must be positive integers")
        return value

    @field_validator("evidence", mode="after")
    @classmethod
    def evidence_is_nonblank_and_deterministic(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(sorted(set(values)))
        if not normalized or any(not isinstance(item, str) or not item.strip() for item in normalized):
            raise ValueError("evidence must contain nonblank values")
        return normalized


class CompatibilityIssue(ContractModel):
    constraint_id: str
    field: str
    required_value: str
    declared_value: str | None
    reason: str

    @field_validator("constraint_id", "field", "required_value", "reason")
    @classmethod
    def fields_are_nonblank(cls, value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("compatibility issue fields must be nonblank")
        return value


class CompatibilityResult(ContractModel):
    record: ModelCapabilityRecord
    requirements: ModelCapabilityRequirements
    status: CompatibilityStatus
    issues: tuple[CompatibilityIssue, ...]

    @field_validator("issues", mode="after")
    @classmethod
    def issues_are_deterministic(
        cls, values: tuple[CompatibilityIssue, ...]
    ) -> tuple[CompatibilityIssue, ...]:
        if any(not isinstance(item, CompatibilityIssue) for item in values):
            raise ValueError("issues must contain CompatibilityIssue values")
        return tuple(sorted(values, key=lambda item: (item.constraint_id, item.field)))


def _issue(
    constraint_id: str, field: str, required_value: str, declared_value: str | None
) -> CompatibilityIssue:
    declared = declared_value if declared_value is not None else "unknown"
    return CompatibilityIssue(
        constraint_id=constraint_id,
        field=field,
        required_value=required_value,
        declared_value=declared_value,
        reason=f"{field} requires {required_value}, but the model declares {declared}",
    )


def evaluate_compatibility(
    record: ModelCapabilityRecord, requirements: ModelCapabilityRequirements
) -> CompatibilityResult:
    """Evaluate hard declared requirements without comparing this model to another."""

    if not isinstance(record, ModelCapabilityRecord):
        raise ValueError("record must be a ModelCapabilityRecord")
    if not isinstance(requirements, ModelCapabilityRequirements):
        raise ValueError("requirements must be ModelCapabilityRequirements")

    issues: list[CompatibilityIssue] = []
    for modality in requirements.required_input_modalities:
        if modality not in record.input_modalities:
            issues.append(_issue("input_modality", "input_modalities", modality.value, ",".join(item.value for item in record.input_modalities)))
    for modality in requirements.required_output_modalities:
        if modality not in record.output_modalities:
            issues.append(_issue("output_modality", "output_modalities", modality.value, ",".join(item.value for item in record.output_modalities)))
    for capability in requirements.required_reasoning_capabilities:
        if capability not in record.reasoning_capabilities:
            issues.append(_issue("reasoning_capability", "reasoning_capabilities", capability.value, ",".join(item.value for item in record.reasoning_capabilities)))

    boolean_requirements = (
        ("tool_use", "supports_tool_use", requirements.requires_tool_use),
        ("retrieval", "supports_retrieval", requirements.requires_retrieval),
        ("code_generation", "supports_code_generation", requirements.requires_code_generation),
        ("code_understanding", "supports_code_understanding", requirements.requires_code_understanding),
        ("structured_tool_arguments", "supports_structured_tool_arguments", requirements.requires_structured_tool_arguments),
        ("tool_result_consumption", "supports_tool_result_consumption", requirements.requires_tool_result_consumption),
        ("json_output", "supports_json_output", requirements.requires_json_output),
        ("schema_constrained_output", "supports_schema_constrained_output", requirements.requires_schema_constrained_output),
        ("streaming", "supports_streaming", requirements.requires_streaming),
    )
    for constraint_id, field, required in boolean_requirements:
        if required and not getattr(record, field):
            issues.append(_issue(constraint_id, field, "true", "false"))

    for constraint_id, field, minimum in (
        ("context_limit", "max_context_tokens", requirements.minimum_context_tokens),
        ("output_limit", "max_output_tokens", requirements.minimum_output_tokens),
    ):
        declared = getattr(record, field)
        if minimum is not None and (declared is None or declared < minimum):
            issues.append(_issue(constraint_id, field, str(minimum), None if declared is None else str(declared)))

    if requirements.allowed_statuses is not None and record.status not in requirements.allowed_statuses:
        issues.append(_issue("capability_status", "status", ",".join(item.value for item in requirements.allowed_statuses), record.status.value))

    normalized_issues = tuple(sorted(issues, key=lambda item: (item.constraint_id, item.field, item.required_value)))
    return CompatibilityResult(
        record=record,
        requirements=requirements,
        status=CompatibilityStatus.INCOMPATIBLE if normalized_issues else CompatibilityStatus.COMPATIBLE,
        issues=normalized_issues,
    )
