from collections.abc import Iterable

from mercury.context_prediction.contracts import (
    MAX_CONTEXT_PREDICTIONS,
    MAX_PREDICTION_CANDIDATES,
    ContextPrediction,
    ContextPredictionCandidate,
    ContextPredictionFeatureVector,
    ContextPredictionHorizon,
    ContextPredictionRequest,
    ContextPredictionResult,
    make_context_prediction_id,
)
from mercury.context_prediction.backend import (
    ContextPredictionBackend, DeterministicWeightedPredictionBackend, ScoredContextPrediction,
)


HORIZON_ORDER = {
    ContextPredictionHorizon.NEXT_TURN: 0,
    ContextPredictionHorizon.NEXT_TASK: 1,
    ContextPredictionHorizon.SESSION_NEAR_TERM: 2,
}


def assemble_context_predictions(
    request: ContextPredictionRequest,
    candidates: Iterable[ContextPredictionCandidate],
    feature_vectors: Iterable[ContextPredictionFeatureVector],
    *,
    backend: ContextPredictionBackend | None = None,
) -> ContextPredictionResult:
    if not isinstance(request, ContextPredictionRequest):
        raise ValueError("context prediction request required")
    request = ContextPredictionRequest.model_validate(request.model_dump())

    candidate_tuple = tuple(candidates)
    feature_tuple = tuple(feature_vectors)
    if len(candidate_tuple) > MAX_PREDICTION_CANDIDATES:
        raise ValueError("too many prediction candidates")
    if any(type(item) is not ContextPredictionCandidate for item in candidate_tuple):
        raise ValueError("invalid prediction candidate")
    candidate_tuple = tuple(ContextPredictionCandidate.model_validate(item.model_dump()) for item in candidate_tuple)

    candidate_ids = [item.candidate_id for item in candidate_tuple]
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError("duplicate prediction candidate")

    feature_by_id = {}
    for feature in feature_tuple:
        if not isinstance(feature, ContextPredictionFeatureVector):
            raise ValueError("invalid prediction feature vector")
        if feature.candidate_id in feature_by_id:
            raise ValueError("duplicate prediction feature vector")
        feature_by_id[feature.candidate_id] = feature

    if set(feature_by_id) != set(candidate_ids):
        raise ValueError("candidate and feature identities must match exactly")

    for candidate in candidate_tuple:
        if (candidate.namespace_type, candidate.namespace_id) != (request.namespace_type, request.namespace_id):
            raise ValueError("candidate namespace authorization mismatch")
    selected_backend = DeterministicWeightedPredictionBackend() if backend is None else backend
    if not isinstance(selected_backend, ContextPredictionBackend):
        raise ValueError("prediction backend required")
    scores = tuple(selected_backend.predict(feature_tuple, candidate_tuple, request.prediction_horizon))
    if any(type(score) is not ScoredContextPrediction for score in scores):
        raise ValueError("typed backend scores required")
    scores = tuple(ScoredContextPrediction.model_validate(score.model_dump()) for score in scores)
    scores_by_id = {score.candidate_id: score for score in scores}
    if len(scores_by_id) != len(scores) or not set(scores_by_id).issubset(candidate_ids):
        raise ValueError("foreign or duplicate backend candidate score")
    if request.prediction_horizon is None and set(scores_by_id) != set(candidate_ids):
        raise ValueError("missing backend score")
    if request.prediction_horizon is not None and any(score.prediction_horizon is not request.prediction_horizon for score in scores):
        raise ValueError("backend horizon mismatch")

    predictions = []
    for candidate in candidate_tuple:
        if not isinstance(candidate, ContextPredictionCandidate):
            raise ValueError("invalid prediction candidate")
        if (
            candidate.namespace_type is not request.namespace_type
            or candidate.namespace_id != request.namespace_id
        ):
            raise ValueError("candidate namespace authorization mismatch")

        if candidate.candidate_id not in scores_by_id:
            continue
        score = scores_by_id[candidate.candidate_id]
        horizon, confidence, band, reasons = score.prediction_horizon, score.raw_score, score.confidence_band, score.reason_codes

        prediction_id = make_context_prediction_id(
            namespace_type=candidate.namespace_type,
            namespace_id=candidate.namespace_id,
            context_key=candidate.context_key,
            source_global_record_ids=candidate.source_global_record_ids,
            source_phase8_record_ids=candidate.source_phase8_record_ids,
            prediction_horizon=horizon,
            confidence=confidence,
            confidence_band=band,
            reason_codes=reasons,
            creation_sequence=candidate.creation_sequence,
            predictor_id=request.predictor_id,
            predictor_version=request.predictor_version,
        )
        predictions.append(
            ContextPrediction(
                prediction_id=prediction_id,
                source_evidence=candidate.source_evidence,
                namespace_type=candidate.namespace_type,
                namespace_id=candidate.namespace_id,
                context_key=candidate.context_key,
                source_global_record_ids=candidate.source_global_record_ids,
                source_phase8_record_ids=candidate.source_phase8_record_ids,
                prediction_horizon=horizon,
                confidence=confidence,
                raw_score=score.raw_score,
                calibration_status=score.calibration_status,
                calibration_evidence=score.calibration_evidence,
                confidence_band=band,
                reason_codes=reasons,
                creation_sequence=candidate.creation_sequence,
                predictor_id=request.predictor_id,
                predictor_version=request.predictor_version,
            )
        )

    ordered = tuple(
        sorted(
            predictions,
            key=lambda item: (
                HORIZON_ORDER[item.prediction_horizon],
                -item.confidence,
                item.namespace_type.value,
                item.namespace_id,
                item.context_key,
                item.prediction_id,
            ),
        )
    )

    limit = min(request.limit, MAX_CONTEXT_PREDICTIONS)
    return ContextPredictionResult(predictions=ordered[:limit])
