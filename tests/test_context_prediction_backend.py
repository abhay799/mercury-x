import pytest

from mercury.context_prediction.integration import predict_context
from mercury.context_prediction.contracts import ContextPredictionHorizon, ContextConfidenceBand
from tests._context_prediction_helpers import request, global_record, store


def test_predictions_report_raw_uncalibrated_score_without_probability_claim():
    result = predict_context(request(), global_store=store(global_record()))
    prediction = result.predictions[0]
    assert prediction.raw_score == prediction.confidence
    assert prediction.calibration_status.value == "UNCALIBRATED"
    assert prediction.calibration_evidence == ()


def test_default_backend_is_explicit_and_substitutable():
    from mercury.context_prediction.backend import ContextPredictionBackend, DeterministicWeightedPredictionBackend

    class RecordingBackend:
        def __init__(self):
            self.calls = []

        def predict(self, features, candidates, horizon=None):
            self.calls.append((features, candidates, horizon))
            return DeterministicWeightedPredictionBackend().predict(features, candidates, horizon)

    backend = RecordingBackend()
    assert isinstance(backend, ContextPredictionBackend)
    records = store(global_record())
    expected = predict_context(request(), global_store=records)
    actual = predict_context(request(), global_store=records, backend=backend)
    assert actual == expected
    assert len(backend.calls) == 1
    assert backend.calls[0][1][0].source_global_record_ids == ("g1",)


def test_horizon_filter_does_not_promote_unrelated_predictions():
    req = request(prediction_horizon=ContextPredictionHorizon.NEXT_TASK)
    records = store(global_record("g1", "current"), global_record("g2", "dependency"))
    result = predict_context(req, global_store=records, current_context_key="current", dependency_context_keys=("dependency",))
    assert [p.context_key for p in result.predictions] == ["dependency"]
    assert result.predictions[0].prediction_horizon is ContextPredictionHorizon.NEXT_TASK


def test_backend_cannot_emit_foreign_or_duplicate_candidate_scores():
    from mercury.context_prediction.backend import DeterministicWeightedPredictionBackend

    class DuplicateBackend:
        def predict(self, features, candidates, horizon=None):
            scores = DeterministicWeightedPredictionBackend().predict(features, candidates, horizon)
            return scores + scores

    with pytest.raises(ValueError):
        predict_context(request(), global_store=store(global_record()), backend=DuplicateBackend())


def test_uncalibrated_metadata_cannot_claim_empirical_calibration_without_evidence():
    from mercury.context_prediction.contracts import ContextPrediction
    prediction = predict_context(request(), global_store=store(global_record())).predictions[0]
    values = prediction.model_dump()
    values["calibration_status"] = "EMPIRICALLY_CALIBRATED"
    values["calibration_evidence"] = ()
    with pytest.raises(ValueError):
        ContextPrediction(**values)


@pytest.mark.parametrize(("value", "band"), [(0.399999, ContextConfidenceBand.LOW), (0.4, ContextConfidenceBand.MEDIUM), (0.749999, ContextConfidenceBand.MEDIUM), (0.75, ContextConfidenceBand.HIGH)])
def test_exact_confidence_band_thresholds(value, band):
    from mercury.context_prediction.scoring import score_prediction
    from tests.test_context_prediction_scoring import vector
    features = vector(**{name: value for name in (
        "recency", "task_continuity", "context_key_recurrence", "dependency_adjacency",
        "source_lineage_overlap", "artifact_continuity", "session_global_agreement",
        "lifecycle_eligibility", "conflict_state", "horizon_compatibility")})
    assert score_prediction(features)[2] is band
