from mercury.context_prediction.contracts import (
    ContextConfidenceBand,
    ContextPredictionFeatureVector,
    ContextPredictionHorizon,
    ContextPredictionReasonCode,
)
from mercury.context_prediction.scoring import score_prediction


def vector(**overrides):
    data = dict(
        candidate_id="c1",
        recency=None,
        task_continuity=0.0,
        context_key_recurrence=0.0,
        dependency_adjacency=0.0,
        source_lineage_overlap=0.0,
        artifact_continuity=0.0,
        session_global_agreement=0.0,
        lifecycle_eligibility=1.0,
        conflict_state=1.0,
        horizon_compatibility=0.25,
    )
    data.update(overrides)
    return ContextPredictionFeatureVector(**data)


def test_task_continuity_selects_next_turn():
    horizon, confidence, band, reasons = score_prediction(
        vector(task_continuity=1.0, horizon_compatibility=1.0)
    )
    assert horizon is ContextPredictionHorizon.NEXT_TURN
    assert 0 <= confidence <= 1
    assert ContextPredictionReasonCode.TASK_CONTINUITY in reasons


def test_dependency_selects_next_task():
    horizon, *_ = score_prediction(vector(dependency_adjacency=1.0))
    assert horizon is ContextPredictionHorizon.NEXT_TASK


def test_weak_signal_selects_session_near_term():
    horizon, *_ = score_prediction(vector())
    assert horizon is ContextPredictionHorizon.SESSION_NEAR_TERM


def test_conflict_reason_is_preserved():
    _, _, _, reasons = score_prediction(vector(conflict_state=0.0))
    assert ContextPredictionReasonCode.CONFLICT_PRESENT in reasons


def test_scoring_is_deterministic():
    assert score_prediction(vector()) == score_prediction(vector())
