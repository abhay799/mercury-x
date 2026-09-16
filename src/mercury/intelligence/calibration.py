"""Deterministic confidence and evidence calibration for Phase 2 profiles."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from mercury.intelligence.models import (
    ComputationalCapability,
    ReasoningComplexity,
    WorkloadIntelligenceProfile,
    WorkloadModality,
)
from mercury.intelligence.signals import WorkloadSignals


class CalibrationStatus(str, Enum):
    PASS = "pass"
    DEGRADED = "degraded"
    FAIL = "fail"


class EvidenceStrength(str, Enum):
    EXPLICIT = "explicit"
    DERIVED = "derived"
    DEFAULTED = "defaulted"


class CalibrationSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class CalibrationDecision:
    affected_field: str
    strength: EvidenceStrength
    severity: CalibrationSeverity
    reason: str

    def __post_init__(self) -> None:
        if not self.affected_field.strip():
            raise ValueError("affected_field must be nonblank")
        if not self.reason.strip():
            raise ValueError("reason must be nonblank")


@dataclass(frozen=True)
class CalibratedWorkloadIntelligence:
    profile: WorkloadIntelligenceProfile
    calibrated_confidence: float
    status: CalibrationStatus
    decisions: tuple[CalibrationDecision, ...]

    def __post_init__(self) -> None:
        if not 0.0 <= self.calibrated_confidence <= 1.0:
            raise ValueError("calibrated_confidence must be between 0.0 and 1.0")
        decisions = tuple(
            sorted(set(self.decisions), key=lambda item: (item.affected_field, item.reason))
        )
        if not decisions:
            raise ValueError("decisions must not be empty")
        if self.status is CalibrationStatus.FAIL and self.calibrated_confidence != 0.0:
            raise ValueError("failed calibration must fail closed with zero confidence")
        object.__setattr__(self, "decisions", decisions)


_EVIDENCE_SOURCES = {
    "modalities": "signals.content",
    "reasoning_complexity": "signals.reasoning",
    "context_requirement": "signals.context",
    "tool_requirements": "signals.tools",
    "latency_sensitivity": "signals.latency_constraint",
    "quality_requirement": "signals.quality_constraint",
    "privacy_requirement": "signals.privacy_constraint",
    "required_capabilities": "signals.capabilities",
}
_PRIVACY_RANK = {"public": 0, "internal": 1, "confidential": 2, "restricted": 3}
_REASONING_RANK = {
    ReasoningComplexity.MINIMAL: 0,
    ReasoningComplexity.LOW: 1,
    ReasoningComplexity.MODERATE: 2,
    ReasoningComplexity.HIGH: 3,
    ReasoningComplexity.DEEP: 4,
}


def _expected_modality(signals: WorkloadSignals) -> WorkloadModality | None:
    if not signals.explicit_modalities:
        return None
    if len(signals.explicit_modalities) > 1:
        return WorkloadModality.MULTIMODAL
    return {
        "text": WorkloadModality.TEXT,
        "image": WorkloadModality.IMAGE,
        "audio": WorkloadModality.AUDIO,
        "video": WorkloadModality.VIDEO,
        "structured_data": WorkloadModality.STRUCTURED_DATA,
        "code": WorkloadModality.CODE,
    }.get(signals.explicit_modalities[0])


def _expected_reasoning(signals: WorkloadSignals) -> ReasoningComplexity:
    tools = bool(signals.tool_use_requested or signals.declared_tool_names)
    retrieval = bool(signals.context_references)
    if signals.long_context_requested and tools and retrieval:
        return ReasoningComplexity.DEEP
    if signals.long_context_requested and (tools or retrieval):
        return ReasoningComplexity.HIGH
    if tools and retrieval:
        return ReasoningComplexity.MODERATE
    if tools or retrieval or signals.explicit_context_supplied:
        return ReasoningComplexity.LOW
    return ReasoningComplexity.MINIMAL


def _strengths(signals: WorkloadSignals) -> dict[str, EvidenceStrength]:
    return {
        "modalities": EvidenceStrength.EXPLICIT if signals.explicit_modalities else EvidenceStrength.DEFAULTED,
        "reasoning_complexity": EvidenceStrength.DERIVED if _expected_reasoning(signals) is not ReasoningComplexity.MINIMAL else EvidenceStrength.DEFAULTED,
        "context_requirement": EvidenceStrength.EXPLICIT if signals.explicit_context_supplied else EvidenceStrength.DEFAULTED,
        "tool_requirements": EvidenceStrength.EXPLICIT if (signals.tool_use_requested or signals.declared_tool_names or signals.external_action_required) else EvidenceStrength.DEFAULTED,
        "latency_sensitivity": EvidenceStrength.EXPLICIT if signals.latency_constraint is not None else EvidenceStrength.DEFAULTED,
        "quality_requirement": EvidenceStrength.EXPLICIT if signals.quality_constraint is not None else EvidenceStrength.DEFAULTED,
        "privacy_requirement": EvidenceStrength.EXPLICIT if signals.privacy_constraint is not None else EvidenceStrength.DEFAULTED,
        "required_capabilities": EvidenceStrength.DERIVED,
    }


def _profile_evidence_is_valid(profile: WorkloadIntelligenceProfile) -> bool:
    evidence = profile.evidence
    if not evidence or any(not item.source.strip() or not item.reason.strip() for item in evidence):
        return False
    sources = {item.source for item in evidence}
    return all(source in sources for source in _EVIDENCE_SOURCES.values())


def calibrate_workload_intelligence(
    signals: WorkloadSignals, profile: WorkloadIntelligenceProfile
) -> CalibratedWorkloadIntelligence:
    """Return deterministic calibration metadata without rewriting ``profile``."""
    decisions: list[CalibrationDecision] = []
    failures: list[tuple[str, str]] = []

    if not isinstance(signals, WorkloadSignals) or not isinstance(profile, WorkloadIntelligenceProfile):
        raise ValueError("signals and profile must use Phase 2 contracts")
    if (signals.request_id, signals.workload_id, signals.session_id) != (
        profile.request_id,
        profile.workload_id,
        profile.session_id,
    ):
        failures.append(("identity", "signals and profile identities do not match"))
    if not _profile_evidence_is_valid(profile):
        failures.append(("evidence", "profile evidence is missing, blank, or incomplete"))

    expected_modality = _expected_modality(signals)
    if expected_modality is None:
        failures.append(("modalities", "signals do not provide explicit modality evidence"))
    elif profile.modalities != (expected_modality,):
        failures.append(("modalities", "profile modality contradicts explicit content signals"))

    has_tool_evidence = bool(signals.tool_use_requested or signals.declared_tool_names or signals.external_action_required)
    if not has_tool_evidence and (
        profile.tool_requirements.external_execution_required
        or ComputationalCapability.TOOL_USE in profile.required_capabilities
    ):
        failures.append(("tool_requirements", "tool capability is unsupported by explicit tool signals"))
    if not signals.context_references and ComputationalCapability.RETRIEVAL in profile.required_capabilities:
        failures.append(("required_capabilities", "retrieval capability lacks explicit retrieval evidence"))
    if (
        not signals.structured_output_required
        and not signals.structured_data_present
        and ComputationalCapability.STRUCTURED_OUTPUT in profile.required_capabilities
    ):
        failures.append(("required_capabilities", "structured-output capability lacks explicit output evidence"))
    if (
        not (signals.image_input_present or signals.video_input_present)
        and ComputationalCapability.VISION in profile.required_capabilities
    ):
        failures.append(("required_capabilities", "vision capability lacks explicit visual evidence"))
    if not signals.audio_input_present and ComputationalCapability.SPEECH in profile.required_capabilities:
        failures.append(("required_capabilities", "speech capability lacks explicit audio evidence"))
    if (
        "code_execution" not in signals.declared_tool_names
        and ComputationalCapability.CODE_EXECUTION in profile.required_capabilities
    ):
        failures.append(("required_capabilities", "code-execution capability lacks explicit code-execution evidence"))
    if signals.latency_constraint is None and profile.latency_sensitivity.value == "realtime":
        failures.append(("latency_sensitivity", "realtime sensitivity lacks explicit latency evidence"))
    if signals.quality_constraint is None and profile.quality_requirement.value == "critical":
        failures.append(("quality_requirement", "critical quality lacks explicit quality evidence"))
    if signals.privacy_constraint is not None and isinstance(signals.privacy_constraint.value, str):
        signal_rank = _PRIVACY_RANK.get(signals.privacy_constraint.value)
        profile_rank = _PRIVACY_RANK[profile.privacy_requirement.value]
        if signal_rank is None:
            failures.append(("privacy_requirement", "explicit privacy signal is unsupported"))
        elif profile_rank < signal_rank:
            failures.append(("privacy_requirement", "profile privacy is downgraded below explicit privacy evidence"))
    expected_reasoning = _expected_reasoning(signals)
    if _REASONING_RANK[profile.reasoning_complexity] > _REASONING_RANK[expected_reasoning]:
        failures.append(("reasoning_complexity", "profile reasoning complexity exceeds explicit signal support"))

    strengths = _strengths(signals)
    for field, strength in strengths.items():
        decisions.append(
            CalibrationDecision(
                affected_field=field,
                strength=strength,
                severity=(CalibrationSeverity.WARNING if strength is EvidenceStrength.DEFAULTED else CalibrationSeverity.INFO),
                reason=(
                    "field is conservatively defaulted because explicit signal evidence is absent"
                    if strength is EvidenceStrength.DEFAULTED
                    else "field is supported by deterministic explicit or derived signal evidence"
                ),
            )
        )
    for field, reason in failures:
        decisions.append(
            CalibrationDecision(field, EvidenceStrength.DEFAULTED, CalibrationSeverity.ERROR, reason)
        )

    if failures:
        status = CalibrationStatus.FAIL
        calibrated_confidence = 0.0
    else:
        defaulted = sum(value is EvidenceStrength.DEFAULTED for value in strengths.values())
        derived = sum(value is EvidenceStrength.DERIVED for value in strengths.values())
        ceiling = max(0.0, round(1.0 - defaulted * 0.10 - derived * 0.03, 2))
        calibrated_confidence = min(profile.confidence, ceiling)
        status = CalibrationStatus.DEGRADED if defaulted else CalibrationStatus.PASS
    return CalibratedWorkloadIntelligence(
        profile=profile,
        calibrated_confidence=calibrated_confidence,
        status=status,
        decisions=tuple(decisions),
    )
