"""Deterministic, evidence-backed inference from workload signals only."""

from __future__ import annotations

from mercury.intelligence.models import (
    ComputationalCapability,
    ContextMagnitude,
    ContextRequirement,
    Evidence,
    LatencySensitivity,
    PrivacyRequirement,
    QualityRequirement,
    ReasoningComplexity,
    ToolRequirement,
    WorkloadIntelligenceProfile,
    WorkloadModality,
)
from mercury.intelligence.signals import WorkloadSignals


_SINGLE_MODALITIES = {
    "text": WorkloadModality.TEXT,
    "image": WorkloadModality.IMAGE,
    "audio": WorkloadModality.AUDIO,
    "video": WorkloadModality.VIDEO,
    "structured_data": WorkloadModality.STRUCTURED_DATA,
    "code": WorkloadModality.CODE,
}


def _modalities(signals: WorkloadSignals) -> tuple[WorkloadModality, ...]:
    explicit = signals.explicit_modalities
    if not explicit:
        raise ValueError("modality evidence is required")
    if len(explicit) > 1:
        return (WorkloadModality.MULTIMODAL,)
    try:
        return (_SINGLE_MODALITIES[explicit[0]],)
    except KeyError as error:
        raise ValueError("modality evidence is not supported") from error


def _reasoning(signals: WorkloadSignals) -> ReasoningComplexity:
    has_tools = bool(signals.tool_use_requested or signals.declared_tool_names)
    has_retrieval = bool(signals.context_references)
    if signals.long_context_requested and has_tools and has_retrieval:
        return ReasoningComplexity.DEEP
    if signals.long_context_requested and (has_tools or has_retrieval):
        return ReasoningComplexity.HIGH
    if has_tools and has_retrieval:
        return ReasoningComplexity.MODERATE
    if has_tools or has_retrieval or signals.explicit_context_supplied:
        return ReasoningComplexity.LOW
    return ReasoningComplexity.MINIMAL


def _context(signals: WorkloadSignals) -> ContextRequirement:
    if signals.long_context_requested:
        return ContextRequirement(ContextMagnitude.LONG, True)
    if signals.conversation_context_present or signals.context_references:
        return ContextRequirement(ContextMagnitude.EXTENDED)
    if signals.explicit_context_supplied:
        return ContextRequirement(ContextMagnitude.STANDARD)
    return ContextRequirement(ContextMagnitude.SHORT)


def _latency(signals: WorkloadSignals) -> LatencySensitivity:
    constraint = signals.latency_constraint
    if constraint is None or not isinstance(constraint.value, (int, float)):
        return LatencySensitivity.BATCH
    if constraint.value <= 250:
        return LatencySensitivity.REALTIME
    if constraint.value <= 1_000:
        return LatencySensitivity.INTERACTIVE
    if constraint.value <= 10_000:
        return LatencySensitivity.RELAXED
    return LatencySensitivity.BATCH


def _quality(signals: WorkloadSignals) -> QualityRequirement:
    constraint = signals.quality_constraint
    if constraint is None or not isinstance(constraint.value, (int, float)):
        return QualityRequirement.STANDARD
    if constraint.value >= 0.95:
        return QualityRequirement.CRITICAL
    if constraint.value >= 0.80:
        return QualityRequirement.HIGH
    return QualityRequirement.STANDARD


def _privacy(signals: WorkloadSignals) -> PrivacyRequirement:
    constraint = signals.privacy_constraint
    if constraint is None:
        return PrivacyRequirement.RESTRICTED
    if not isinstance(constraint.value, str):
        raise ValueError("privacy constraint must be an explicit privacy value")
    try:
        return PrivacyRequirement(constraint.value)
    except ValueError as error:
        raise ValueError("privacy constraint is not supported") from error


def _capabilities(
    signals: WorkloadSignals, modalities: tuple[WorkloadModality, ...]
) -> tuple[ComputationalCapability, ...]:
    capabilities: set[ComputationalCapability] = set()
    modality = modalities[0]
    if modality is WorkloadModality.IMAGE or modality is WorkloadModality.VIDEO:
        capabilities.add(ComputationalCapability.VISION)
    elif modality is WorkloadModality.AUDIO:
        capabilities.add(ComputationalCapability.SPEECH)
    elif modality is WorkloadModality.STRUCTURED_DATA:
        capabilities.add(ComputationalCapability.STRUCTURED_OUTPUT)
    else:
        capabilities.add(ComputationalCapability.GENERATION)
    if modality is WorkloadModality.MULTIMODAL:
        if signals.image_input_present or signals.video_input_present:
            capabilities.add(ComputationalCapability.VISION)
        if signals.audio_input_present:
            capabilities.add(ComputationalCapability.SPEECH)
        capabilities.add(ComputationalCapability.GENERATION)
    if signals.tool_use_requested or signals.declared_tool_names:
        capabilities.add(ComputationalCapability.TOOL_USE)
    if signals.context_references:
        capabilities.add(ComputationalCapability.RETRIEVAL)
    if signals.structured_output_required:
        capabilities.add(ComputationalCapability.STRUCTURED_OUTPUT)
    if "code_execution" in signals.declared_tool_names:
        capabilities.add(ComputationalCapability.CODE_EXECUTION)
    if _reasoning(signals) is not ReasoningComplexity.MINIMAL:
        capabilities.add(ComputationalCapability.REASONING)
    return tuple(sorted(capabilities, key=lambda item: item.value))


def _confidence(signals: WorkloadSignals) -> float:
    score = 0.20  # Explicit modality evidence is required before inference proceeds.
    score += 0.15 if signals.latency_constraint is not None else 0.0
    score += 0.10 if signals.quality_constraint is not None else 0.0
    score += 0.10 if signals.privacy_constraint is not None else 0.0
    score += 0.10 if signals.explicit_context_supplied else 0.0
    score += 0.10 if (signals.tool_use_requested or signals.declared_tool_names) else 0.0
    score += 0.10 if signals.context_references else 0.0
    score += 0.05 if (signals.output_type or signals.structured_output_required is not None) else 0.0
    return min(1.0, round(score, 2))


def infer_workload_intelligence(signals: WorkloadSignals) -> WorkloadIntelligenceProfile:
    """Convert explicit Task 2 signals into a bounded Task 1 profile."""
    if not isinstance(signals, WorkloadSignals):
        raise ValueError("signals must be a WorkloadSignals instance")
    if any(not isinstance(value, str) or not value.strip() for value in (signals.request_id, signals.workload_id, signals.session_id)):
        raise ValueError("signals identity must be nonblank")

    modalities = _modalities(signals)
    reasoning = _reasoning(signals)
    context = _context(signals)
    tool_requested = bool(signals.tool_use_requested or signals.declared_tool_names or signals.external_action_required)
    tool_requirements = ToolRequirement(
        tool_requested,
        (ComputationalCapability.TOOL_USE,) if tool_requested else (),
    )
    latency = _latency(signals)
    quality = _quality(signals)
    privacy = _privacy(signals)
    capabilities = _capabilities(signals, modalities)
    confidence = _confidence(signals)
    evidence = (
        Evidence("signals.content", "explicit modality signals determine the workload modality"),
        Evidence("signals.context", "explicit context indicators determine the context requirement"),
        Evidence("signals.tools", "explicit tool indicators determine the tool requirement"),
        Evidence("signals.latency_constraint", "canonical latency constraint maps through the baseline threshold table"),
        Evidence("signals.quality_constraint", "canonical quality constraint maps through the baseline threshold table"),
        Evidence("signals.privacy_constraint", "canonical privacy constraint is preserved without reduction"),
        Evidence("signals.output", "explicit output indicators determine structured-output capability"),
        Evidence("signals.capabilities", "explicit modality, tool, output, and context signals determine capabilities"),
        Evidence("signals.completeness", "deterministic confidence reflects explicitly evidenced signal groups"),
        Evidence("signals.reasoning", "reasoning complexity uses only explicit context, retrieval, and tool signals"),
    )
    return WorkloadIntelligenceProfile(
        request_id=signals.request_id,
        workload_id=signals.workload_id,
        session_id=signals.session_id,
        modalities=modalities,
        reasoning_complexity=reasoning,
        context_requirement=context,
        tool_requirements=tool_requirements,
        latency_sensitivity=latency,
        quality_requirement=quality,
        privacy_requirement=privacy,
        required_capabilities=capabilities,
        confidence=confidence,
        evidence=evidence,
    )
