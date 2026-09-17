import pytest

from mercury.context_prediction.contracts import ContextPredictionHorizon
from mercury.context_prediction.integration import predict_context
from mercury.global_memory.contracts import GlobalMemoryNamespace
from mercury.session_memory.contracts import SessionMemoryLifecycle
from tests._context_prediction_helpers import (
    global_record,
    request,
    scope,
    session_record,
    store,
)


def test_end_to_end_prediction_path():
    record = session_record()
    result = predict_context(
        request(),
        session_records=(record,),
        session_scope=scope(),
        current_context_key="risk",
        current_phase8_record_ids=("s1",),
    )
    assert len(result.predictions) == 1
    assert result.predictions[0].prediction_horizon is ContextPredictionHorizon.NEXT_TURN


def test_cross_project_fails_closed():
    bad = global_record(namespace_id="p2")
    with pytest.raises(ValueError, match="cross-namespace"):
        predict_context(request(), global_store=store(bad))


def test_closed_namespace_fails_closed():
    closed = store().close_namespace(
        GlobalMemoryNamespace.PROJECT,
        "p1",
        closure_reason="project ended",
        closure_sequence=1,
    )
    with pytest.raises(ValueError, match="closed namespace"):
        predict_context(request(), global_store=closed)


@pytest.mark.parametrize(
    "lifecycle",
    (SessionMemoryLifecycle.EXPIRED, SessionMemoryLifecycle.TOMBSTONED),
)
def test_terminal_source_not_predicted(lifecycle):
    dead = session_record(lifecycle=lifecycle)
    assert predict_context(
        request(), session_records=(dead,), session_scope=scope()
    ).predictions == ()


def test_input_record_is_immutable():
    record = session_record()
    before = record.model_dump()
    predict_context(request(), session_records=(record,), session_scope=scope())
    assert record.model_dump() == before


def test_same_session_different_namespace_scope_fails_closed():
    with pytest.raises(ValueError, match="session namespace scope mismatch"):
        predict_context(
            request(),
            session_records=(session_record(),),
            session_scope=scope(namespace_id="p2"),
        )


def test_different_session_fails_closed():
    with pytest.raises(ValueError, match="session scope mismatch"):
        predict_context(
            request(),
            session_records=(session_record(session_id="session-other"),),
            session_scope=scope(),
        )
