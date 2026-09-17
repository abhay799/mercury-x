import math

from mercury.context_prediction.contracts import (
    MAX_REASON_CODES,
    ContextConfidenceBand,
    ContextPredictionFeatureVector,
    ContextPredictionHorizon,
    ContextPredictionReasonCode,
)


WEIGHTS = {
    "recency": 0.10,
    "task_continuity": 0.20,
    "context_key_recurrence": 0.10,
    "dependency_adjacency": 0.15,
    "source_lineage_overlap": 0.10,
    "artifact_continuity": 0.10,
    "session_global_agreement": 0.10,
    "lifecycle_eligibility": 0.05,
    "conflict_state": 0.05,
    "horizon_compatibility": 0.05,
}


def _band(confidence: float) -> ContextConfidenceBand:
    if confidence < 0.40:
        return ContextConfidenceBand.LOW
    if confidence < 0.75:
        return ContextConfidenceBand.MEDIUM
    return ContextConfidenceBand.HIGH


def score_prediction(
    features: ContextPredictionFeatureVector,
) -> tuple[
    ContextPredictionHorizon,
    float,
    ContextConfidenceBand,
    tuple[ContextPredictionReasonCode, ...],
]:
    if not isinstance(features, ContextPredictionFeatureVector):
        raise ValueError("prediction feature vector required")
    features = ContextPredictionFeatureVector.model_validate(features.model_dump())

    confidence = 0.0
    for name, weight in WEIGHTS.items():
        value = getattr(features, name)
        # Unavailable evidence contributes zero; never renormalize remaining
        # weights upward, which would reward missing temporal evidence.
        confidence += (0.0 if value is None else value) * weight
    confidence = round(max(0.0, min(1.0, confidence)), 12)

    if not math.isfinite(confidence):
        raise ValueError("confidence must be finite")

    if features.task_continuity >= 0.75:
        horizon = ContextPredictionHorizon.NEXT_TURN
    elif (
        features.dependency_adjacency >= 0.75
        or features.source_lineage_overlap >= 0.75
    ):
        horizon = ContextPredictionHorizon.NEXT_TASK
    else:
        horizon = ContextPredictionHorizon.SESSION_NEAR_TERM

    reasons = set()
    if features.task_continuity >= 0.75:
        reasons.add(ContextPredictionReasonCode.TASK_CONTINUITY)
    if features.context_key_recurrence > 0.0:
        reasons.add(ContextPredictionReasonCode.CONTEXT_RECURRENCE)
    if features.dependency_adjacency >= 0.75:
        reasons.add(ContextPredictionReasonCode.DEPENDENCY_ADJACENCY)
    if features.source_lineage_overlap > 0.0:
        reasons.add(ContextPredictionReasonCode.SOURCE_LINEAGE_OVERLAP)
    if features.artifact_continuity > 0.0:
        reasons.add(ContextPredictionReasonCode.ARTIFACT_CONTINUITY)
    if features.session_global_agreement > 0.0:
        reasons.add(ContextPredictionReasonCode.SESSION_GLOBAL_AGREEMENT)
    if features.conflict_state < 1.0:
        reasons.add(ContextPredictionReasonCode.CONFLICT_PRESENT)
    if not reasons:
        reasons.add(ContextPredictionReasonCode.NEAR_TERM_SESSION_SIGNAL)

    ordered = tuple(sorted(reasons, key=lambda item: item.value))
    if len(ordered) > MAX_REASON_CODES:
        raise ValueError("too many reason codes")

    return horizon, confidence, _band(confidence), ordered
