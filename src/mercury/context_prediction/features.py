from collections.abc import Iterable

from mercury.context_prediction.contracts import (
    ContextPredictionCandidate,
    ContextPredictionFeatureVector,
)


def _validated_text_set(values: Iterable[str], *, field_name: str) -> set[str]:
    result = set()
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must contain nonblank text")
        result.add(value)
    return result


def _overlap_ratio(left, right) -> float:
    left_set = set(left)
    right_set = set(right)
    if not left_set or not right_set:
        return 0.0
    return len(left_set & right_set) / float(len(left_set | right_set))


def extract_prediction_features(
    candidate: ContextPredictionCandidate,
    *,
    current_context_key: str | None = None,
    recent_context_keys: Iterable[str] = (),
    dependency_context_keys: Iterable[str] = (),
    current_artifact_ids: Iterable[str] = (),
    current_phase8_record_ids: Iterable[str] = (),
) -> ContextPredictionFeatureVector:
    if not isinstance(candidate, ContextPredictionCandidate):
        raise ValueError("prediction candidate required")

    if current_context_key is not None:
        if not isinstance(current_context_key, str) or not current_context_key.strip():
            raise ValueError("current_context_key must be nonblank")

    recent = tuple(recent_context_keys)
    if any(not isinstance(x, str) or not x.strip() for x in recent):
        raise ValueError("recent_context_keys must contain nonblank text")

    dependencies = _validated_text_set(
        dependency_context_keys,
        field_name="dependency_context_keys",
    )
    artifacts = _validated_text_set(
        current_artifact_ids,
        field_name="current_artifact_ids",
    )
    phase8_ids = _validated_text_set(
        current_phase8_record_ids,
        field_name="current_phase8_record_ids",
    )

    task_continuity = (
        1.0
        if current_context_key is not None
        and candidate.context_key == current_context_key
        else 0.0
    )
    context_key_recurrence = min(
        recent.count(candidate.context_key) / 4.0,
        1.0,
    )
    dependency_adjacency = 1.0 if candidate.context_key in dependencies else 0.0
    source_lineage_overlap = _overlap_ratio(
        candidate.source_phase8_record_ids,
        phase8_ids,
    )
    artifact_continuity = _overlap_ratio(
        candidate.source_artifact_ids,
        artifacts,
    )
    session_global_agreement = (
        1.0
        if candidate.source_phase8_record_ids
        and candidate.source_global_record_ids
        else 0.0
    )
    lifecycle_eligibility = 1.0
    conflict_state = 0.0 if candidate.conflict_present else 1.0

    # Phase 10 deliberately avoids wall-clock inference. A neutral recency
    # prior is used until a separately certified recency signal exists.
    recency = 0.5

    if task_continuity:
        horizon_compatibility = 1.0
    elif dependency_adjacency:
        horizon_compatibility = 0.75
    elif context_key_recurrence > 0.0:
        horizon_compatibility = 0.5
    else:
        horizon_compatibility = 0.25

    return ContextPredictionFeatureVector(
        candidate_id=candidate.candidate_id,
        recency=recency,
        task_continuity=task_continuity,
        context_key_recurrence=context_key_recurrence,
        dependency_adjacency=dependency_adjacency,
        source_lineage_overlap=source_lineage_overlap,
        artifact_continuity=artifact_continuity,
        session_global_agreement=session_global_agreement,
        lifecycle_eligibility=lifecycle_eligibility,
        conflict_state=conflict_state,
        horizon_compatibility=horizon_compatibility,
    )
