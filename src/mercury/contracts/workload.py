from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Modality(str, Enum):
    TEXT = "text"
    DOCUMENT = "document"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    STRUCTURED_DATA = "structured_data"


class ComputeRequirement(str, Enum):
    DOCUMENT_PARSING = "document_parsing"
    EMBEDDING = "embedding"
    RETRIEVAL = "retrieval"
    VISION = "vision"
    REASONING = "reasoning"
    CODE_EXECUTION = "code_execution"
    TOOL_EXECUTION = "tool_execution"
    VERIFICATION = "verification"
    GENERATION = "generation"


class PrivacyLevel(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    PRIVATE = "private"
    RESTRICTED = "restricted"


class ReasoningLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class WorkloadConstraints(BaseModel):
    max_latency_ms: Optional[int] = Field(default=None, gt=0)
    max_cost: Optional[float] = Field(default=None, ge=0)
    min_quality: Optional[float] = Field(default=None, ge=0, le=1)
    min_reliability: Optional[float] = Field(default=None, ge=0, le=1)

    privacy_level: PrivacyLevel = PrivacyLevel.PRIVATE

    allowed_regions: List[str] = Field(default_factory=list)
    energy_budget_wh: Optional[float] = Field(default=None, ge=0)


class CognitiveWorkload(BaseModel):
    workload_id: UUID = Field(default_factory=uuid4)
    session_id: Optional[UUID] = None

    intent: str = Field(min_length=1)

    modalities: List[Modality] = Field(default_factory=list)

    compute_requirements: List[ComputeRequirement] = Field(
        default_factory=list
    )

    reasoning_level: ReasoningLevel = ReasoningLevel.MEDIUM

    expected_output_tokens: Optional[int] = Field(default=None, gt=0)

    priority: int = Field(default=50, ge=0, le=100)

    constraints: WorkloadConstraints = Field(
        default_factory=WorkloadConstraints
    )

    requires_verification: bool = False