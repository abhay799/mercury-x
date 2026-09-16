"""Immutable contracts for workload-intelligence analysis only."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite
from typing import Iterable, TypeVar


class WorkloadModality(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    STRUCTURED_DATA = "structured_data"
    CODE = "code"
    MULTIMODAL = "multimodal"


class ReasoningComplexity(str, Enum):
    MINIMAL = "minimal"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    DEEP = "deep"


class ContextMagnitude(str, Enum):
    SHORT = "short"
    STANDARD = "standard"
    EXTENDED = "extended"
    LONG = "long"


class LatencySensitivity(str, Enum):
    BATCH = "batch"
    RELAXED = "relaxed"
    INTERACTIVE = "interactive"
    REALTIME = "realtime"


class QualityRequirement(str, Enum):
    STANDARD = "standard"
    HIGH = "high"
    CRITICAL = "critical"


class PrivacyRequirement(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class ComputationalCapability(str, Enum):
    GENERATION = "generation"
    REASONING = "reasoning"
    RETRIEVAL = "retrieval"
    VISION = "vision"
    SPEECH = "speech"
    CODE_EXECUTION = "code_execution"
    STRUCTURED_OUTPUT = "structured_output"
    TOOL_USE = "tool_use"


_EnumValue = TypeVar("_EnumValue", bound=Enum)


def _nonblank(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be nonblank")
    return value


def _normalized_enum_tuple(
    values: Iterable[_EnumValue], enum_type: type[_EnumValue], field_name: str
) -> tuple[_EnumValue, ...]:
    normalized = tuple(sorted(set(values), key=lambda value: value.value))
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    if any(not isinstance(value, enum_type) for value in normalized):
        raise ValueError(f"{field_name} must contain {enum_type.__name__} values")
    return normalized


@dataclass(frozen=True)
class ContextRequirement:
    magnitude: ContextMagnitude
    requires_long_context: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.magnitude, ContextMagnitude):
            raise ValueError("magnitude must be a ContextMagnitude")
        if self.requires_long_context != (self.magnitude is ContextMagnitude.LONG):
            raise ValueError("requires_long_context must match a long context magnitude")

    def to_dict(self) -> dict[str, object]:
        return {
            "magnitude": self.magnitude.value,
            "requires_long_context": self.requires_long_context,
        }


@dataclass(frozen=True)
class ToolRequirement:
    external_execution_required: bool
    required_capabilities: tuple[ComputationalCapability, ...] = ()

    def __post_init__(self) -> None:
        capabilities = tuple(
            sorted(set(self.required_capabilities), key=lambda capability: capability.value)
        )
        if any(not isinstance(item, ComputationalCapability) for item in capabilities):
            raise ValueError("required_capabilities must contain ComputationalCapability values")
        if self.external_execution_required and not capabilities:
            raise ValueError("required_capabilities must not be empty when execution is required")
        if not self.external_execution_required and capabilities:
            raise ValueError("required_capabilities require external execution")
        object.__setattr__(self, "required_capabilities", capabilities)

    def to_dict(self) -> dict[str, object]:
        return {
            "external_execution_required": self.external_execution_required,
            "required_capabilities": [item.value for item in self.required_capabilities],
        }


@dataclass(frozen=True)
class Evidence:
    source: str
    reason: str

    def __post_init__(self) -> None:
        _nonblank(self.source, "source")
        _nonblank(self.reason, "reason")

    def to_dict(self) -> dict[str, str]:
        return {"source": self.source, "reason": self.reason}


@dataclass(frozen=True)
class WorkloadIntelligenceProfile:
    request_id: str
    workload_id: str
    session_id: str
    modalities: tuple[WorkloadModality, ...]
    reasoning_complexity: ReasoningComplexity
    context_requirement: ContextRequirement
    tool_requirements: ToolRequirement
    latency_sensitivity: LatencySensitivity
    quality_requirement: QualityRequirement
    privacy_requirement: PrivacyRequirement
    required_capabilities: tuple[ComputationalCapability, ...]
    confidence: float
    evidence: tuple[Evidence, ...]

    def __post_init__(self) -> None:
        for name in ("request_id", "workload_id", "session_id"):
            _nonblank(getattr(self, name), name)
        object.__setattr__(
            self,
            "modalities",
            _normalized_enum_tuple(self.modalities, WorkloadModality, "modalities"),
        )
        object.__setattr__(
            self,
            "required_capabilities",
            _normalized_enum_tuple(
                self.required_capabilities,
                ComputationalCapability,
                "required_capabilities",
            ),
        )
        if not isinstance(self.reasoning_complexity, ReasoningComplexity):
            raise ValueError("reasoning_complexity must be a ReasoningComplexity")
        if not isinstance(self.context_requirement, ContextRequirement):
            raise ValueError("context_requirement must be a ContextRequirement")
        if not isinstance(self.tool_requirements, ToolRequirement):
            raise ValueError("tool_requirements must be a ToolRequirement")
        if not isinstance(self.latency_sensitivity, LatencySensitivity):
            raise ValueError("latency_sensitivity must be a LatencySensitivity")
        if not isinstance(self.quality_requirement, QualityRequirement):
            raise ValueError("quality_requirement must be a QualityRequirement")
        if not isinstance(self.privacy_requirement, PrivacyRequirement):
            raise ValueError("privacy_requirement must be a PrivacyRequirement")
        if isinstance(self.confidence, bool) or not isinstance(self.confidence, (int, float)):
            raise ValueError("confidence must be a finite number between 0.0 and 1.0")
        if not isfinite(self.confidence) or not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        evidence = tuple(sorted(set(self.evidence), key=lambda item: (item.source, item.reason)))
        if not evidence:
            raise ValueError("evidence must not be empty")
        if any(not isinstance(item, Evidence) for item in evidence):
            raise ValueError("evidence must contain Evidence values")
        object.__setattr__(self, "evidence", evidence)

    def to_dict(self) -> dict[str, object]:
        return {
            "request_id": self.request_id,
            "workload_id": self.workload_id,
            "session_id": self.session_id,
            "modalities": [item.value for item in self.modalities],
            "reasoning_complexity": self.reasoning_complexity.value,
            "context_requirement": self.context_requirement.to_dict(),
            "tool_requirements": self.tool_requirements.to_dict(),
            "latency_sensitivity": self.latency_sensitivity.value,
            "quality_requirement": self.quality_requirement.value,
            "privacy_requirement": self.privacy_requirement.value,
            "required_capabilities": [item.value for item in self.required_capabilities],
            "confidence": self.confidence,
            "evidence": [item.to_dict() for item in self.evidence],
        }
