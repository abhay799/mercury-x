from collections.abc import Iterable
from mercury.session_memory.contracts import SessionMemoryRecord
from mercury.global_memory.store import GlobalContextStore

from mercury.context_prediction.candidates import build_prediction_candidates
from mercury.context_prediction.contracts import (
    ContextPredictionRequest,
    ContextPredictionResult,
    SessionPredictionScope,
)
from mercury.context_prediction.features import extract_prediction_features
from mercury.context_prediction.predictor import assemble_context_predictions
from mercury.context_prediction.backend import ContextPredictionBackend


def predict_context(
    request: ContextPredictionRequest,
    *,
    session_records: Iterable[SessionMemoryRecord] = (),
    global_store: GlobalContextStore | None = None,
    session_scope: SessionPredictionScope | None = None,
    current_context_key: str | None = None,
    recent_context_keys: Iterable[str] = (),
    dependency_context_keys: Iterable[str] = (),
    current_artifact_ids: Iterable[str] = (),
    current_phase8_record_ids: Iterable[str] = (),
    backend: ContextPredictionBackend | None = None,
) -> ContextPredictionResult:
    recent_context_keys = tuple(recent_context_keys)
    dependency_context_keys = tuple(dependency_context_keys)
    current_artifact_ids = tuple(current_artifact_ids)
    current_phase8_record_ids = tuple(current_phase8_record_ids)
    candidates = build_prediction_candidates(
        request,
        session_records=session_records,
        global_store=global_store,
        session_scope=session_scope,
        dependency_context_keys=dependency_context_keys,
    )
    reference_sequences = {}
    for candidate in candidates:
        for source in candidate.source_evidence:
            domain = (source.source_kind, source.sequence_scope)
            reference_sequences[domain] = max(reference_sequences.get(domain, 0), source.creation_sequence)
    features = tuple(
        extract_prediction_features(
            candidate,
            current_context_key=current_context_key,
            recent_context_keys=recent_context_keys,
            dependency_context_keys=dependency_context_keys,
            current_artifact_ids=current_artifact_ids,
            current_phase8_record_ids=current_phase8_record_ids,
            reference_sequences=reference_sequences,
        )
        for candidate in candidates
    )
    return assemble_context_predictions(
        request,
        candidates,
        features,
        backend=backend,
    )
