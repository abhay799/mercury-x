"""Immutable, descriptive model capability contracts for Phase 4."""

from __future__ import annotations

from enum import Enum
from typing import Iterable, Literal, TypeVar

from pydantic import field_validator

from mercury.contracts.base import ContractModel


class ModelModality(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    EMBEDDING = "embedding"
    STRUCTURED_DATA = "structured_data"


class ReasoningCapability(str, Enum):
    GENERAL = "general"
    MULTI_STEP = "multi_step"
    MATHEMATICAL = "mathematical"
    CODE = "code"
    PLANNING = "planning"
    LONG_CONTEXT = "long_context"


class CapabilityStatus(str, Enum):
    PRODUCTION = "production"
    EXPERIMENTAL = "experimental"
    SIMULATED = "simulated"
    RESEARCH = "research"
    PLANNED = "planned"


class ProvenanceKind(str, Enum):
    DECLARED = "declared"
    OBSERVED = "observed"


_EnumValue = TypeVar("_EnumValue", bound=Enum)


def _nonblank(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be nonblank")
    return value


def _normalized_enum_tuple(
    values: Iterable[_EnumValue], enum_type: type[_EnumValue], field_name: str
) -> tuple[_EnumValue, ...]:
    normalized = tuple(sorted(set(values), key=lambda item: item.value))
    if any(not isinstance(item, enum_type) for item in normalized):
        raise ValueError(f"{field_name} must contain {enum_type.__name__} values")
    return normalized


class CapabilityProvenance(ContractModel):
    """Evidence supporting declared or observed capability metadata."""

    source: str
    source_revision: str
    evidence: str
    kind: ProvenanceKind = ProvenanceKind.DECLARED

    @field_validator("source", "source_revision", "evidence")
    @classmethod
    def values_are_nonblank(cls, value: str) -> str:
        return _nonblank(value, "provenance value")


class ModelCapabilityRecord(ContractModel):
    """Versioned facts about one model; this contract never selects that model."""

    schema_version: Literal["mercury.model-capability/v1"] = "mercury.model-capability/v1"
    model_id: str
    provider: str
    family: str
    revision: str
    input_modalities: tuple[ModelModality, ...]
    output_modalities: tuple[ModelModality, ...]
    reasoning_capabilities: tuple[ReasoningCapability, ...] = ()
    supports_tool_use: bool = False
    supports_retrieval: bool = False
    supports_code_generation: bool = False
    supports_code_understanding: bool = False
    supports_structured_tool_arguments: bool = False
    supports_tool_result_consumption: bool = False
    supports_json_output: bool = False
    supports_schema_constrained_output: bool = False
    max_context_tokens: int | None = None
    max_output_tokens: int | None = None
    supports_streaming: bool = False
    supports_batching: bool = False
    supports_deterministic_seed: bool = False
    provenance: CapabilityProvenance
    status: CapabilityStatus = CapabilityStatus.PRODUCTION

    @field_validator("model_id", "provider", "family", "revision")
    @classmethod
    def identity_is_nonblank(cls, value: str) -> str:
        return _nonblank(value, "model identity")

    @field_validator("input_modalities", "output_modalities", mode="after")
    @classmethod
    def normalize_modalities(
        cls, values: tuple[ModelModality, ...]
    ) -> tuple[ModelModality, ...]:
        normalized = _normalized_enum_tuple(values, ModelModality, "modalities")
        if not normalized:
            raise ValueError("modalities must not be empty")
        return normalized

    @field_validator("reasoning_capabilities", mode="after")
    @classmethod
    def normalize_reasoning_capabilities(
        cls, values: tuple[ReasoningCapability, ...]
    ) -> tuple[ReasoningCapability, ...]:
        return _normalized_enum_tuple(
            values, ReasoningCapability, "reasoning_capabilities"
        )

    @field_validator("max_context_tokens", "max_output_tokens")
    @classmethod
    def limits_are_positive_when_declared(cls, value: int | None) -> int | None:
        if value is not None and (isinstance(value, bool) or value <= 0):
            raise ValueError("declared limits must be positive integers")
        return value

    @property
    def is_proven_production(self) -> bool:
        return self.status is CapabilityStatus.PRODUCTION

    def to_dict(self) -> dict[str, object]:
        return self.model_dump(mode="json")
