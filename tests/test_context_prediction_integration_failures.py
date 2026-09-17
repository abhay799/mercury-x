from dataclasses import dataclass

import pytest

from mercury.context_prediction.contracts import (
    ContextPredictionHorizon,
    ContextPredictionRequest,
)
from mercury.context_prediction.integration import predict_context
from mercury.global_memory.contracts import GlobalMemoryNamespace


@dataclass(frozen=True)
class Record:
    record_id: str
    context_key: str
    lifecycle: str = "ACTIVE"
    namespace_type: object | None = None
    namespace_id: str | None = None
    creation_sequence: int = 1


class Store:
    def __init__(self, records=(), closed=False):
        self.records = tuple(records)
        self.closed = closed

    def is_namespace_closed(self, namespace_type, namespace_id):
        return self.closed


def request():
    return ContextPredictionRequest(
        namespace_type=GlobalMemoryNamespace.PROJECT,
        namespace_id="p1",
        authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
        authorized_namespace_id="p1",
        predictor_id="phase10",
        predictor_version="1",
    )


def test_end_to_end_prediction_path():
    record = Record(
        "s1",
        "risk",
        namespace_type=GlobalMemoryNamespace.PROJECT,
        namespace_id="p1",
    )
    result = predict_context(
        request(),
        session_records=(record,),
        current_context_key="risk",
        current_phase8_record_ids=("s1",),
    )
    assert len(result.predictions) == 1
    assert result.predictions[0].prediction_horizon is ContextPredictionHorizon.NEXT_TURN


def test_cross_project_fails_closed():
    bad = Record(
        "s1",
        "risk",
        namespace_type=GlobalMemoryNamespace.PROJECT,
        namespace_id="p2",
    )
    with pytest.raises(ValueError):
        predict_context(request(), session_records=(bad,))


def test_closed_namespace_fails_closed():
    with pytest.raises(ValueError):
        predict_context(request(), global_store=Store(closed=True))


def test_terminal_source_not_predicted():
    dead = Record("s1", "risk", lifecycle="TOMBSTONED")
    assert predict_context(request(), session_records=(dead,)).predictions == ()


def test_input_record_is_immutable():
    record = Record("s1", "risk")
    before = record
    predict_context(request(), session_records=(record,))
    assert record == before
