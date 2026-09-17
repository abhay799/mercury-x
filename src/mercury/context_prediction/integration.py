from collections.abc import Iterable
from typing import Any

from mercury.context_prediction.candidates import build_prediction_candidates
from mercury.context_prediction.contracts import (
    ContextPredictionRequest,
    ContextPredictionResult,
)
from mercury.context_prediction.features import extract_prediction_features
from mercury.context_prediction.predictor import assemble_context_predictions


def predict_context(
    request: ContextPredictionRequest,
    *,
    session_records: Iterable[Any] = (),
    global_store: Any | None = None,
    current_context_key: str | None = None,
    recent_context_keys: Iterable[str] = (),
    dependency_context_keys: Iterable[str] = (),
    current_artifact_ids: Iterable[str] = (),
    current_phase8_record_ids: Iterable[str] = (),
) -> ContextPredictionResult:
    candidates = build_prediction_candidates(
        request,
        session_records=session_records,
        global_store=global_store,
        dependency_context_keys=dependency_context_keys,
    )
    features = tuple(
        extract_prediction_features(
            candidate,
            current_context_key=current_context_key,
            recent_context_keys=recent_context_keys,
            dependency_context_keys=dependency_context_keys,
            current_artifact_ids=current_artifact_ids,
            current_phase8_record_ids=current_phase8_record_ids,
        )
        for candidate in candidates
    )
    return assemble_context_predictions(
        request,
        candidates,
        features,
    )
