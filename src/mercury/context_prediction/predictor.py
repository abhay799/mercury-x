from collections.abc import Iterable

from mercury.context_prediction.contracts import (
    MAX_CONTEXT_PREDICTIONS,
    ContextPrediction,
    ContextPredictionCandidate,
    ContextPredictionFeatureVector,
    ContextPredictionHorizon,
    ContextPredictionRequest,
    ContextPredictionResult,
    make_context_prediction_id,
)
from mercury.context_prediction.scoring import score_prediction


HORIZON_ORDER = {
    ContextPredictionHorizon.NEXT_TURN: 0,
    ContextPredictionHorizon.NEXT_TASK: 1,
    ContextPredictionHorizon.SESSION_NEAR_TERM: 2,
}


def assemble_context_predictions(
    request: ContextPredictionRequest,
    candidates: Iterable[ContextPredictionCandidate],
    feature_vectors: Iterable[ContextPredictionFeatureVector],
) -> ContextPredictionResult:
    if not isinstance(request, ContextPredictionRequest):
        raise ValueError("context prediction request required")

    candidate_tuple = tuple(candidates)
    feature_tuple = tuple(feature_vectors)

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

    predictions = []
    for candidate in candidate_tuple:
        if not isinstance(candidate, ContextPredictionCandidate):
            raise ValueError("invalid prediction candidate")
        if (
            candidate.namespace_type is not request.namespace_type
            or candidate.namespace_id != request.namespace_id
        ):
            raise ValueError("candidate namespace authorization mismatch")

        features = feature_by_id[candidate.candidate_id]
        horizon, confidence, band, reasons = score_prediction(features)

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
