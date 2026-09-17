from mercury.context_prediction.contracts import ContextPredictionRequest
from mercury.global_memory.contracts import (
    GlobalContextRecord, GlobalMemoryNamespace, GlobalMemoryType,
    GlobalMemoryLifecycle, GlobalMemoryConflictState,
)
from mercury.global_memory.store import GlobalContextStore
from mercury.session_memory.contracts import (
    SessionMemoryRecord, SessionMemoryType, SessionMemoryScope, SessionMemoryLifecycle,
)


def request(**changes):
    data = dict(namespace_type=GlobalMemoryNamespace.PROJECT, namespace_id="p1",
                authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
                authorized_namespace_id="p1", predictor_id="phase10", predictor_version="2")
    data.update(changes)
    return ContextPredictionRequest(**data)


def scope(**changes):
    from mercury.context_prediction.contracts import SessionPredictionScope
    data = dict(namespace_type=GlobalMemoryNamespace.PROJECT, namespace_id="p1", session_id="session-1")
    data.update(changes)
    return SessionPredictionScope(**data)


def session_record(record_id="s1", key="risk", **changes):
    data = dict(session_id="session-1", task_id="task-1", turn_id="turn-1", record_id=record_id,
                record_version=1, source_phase="gateway", source_artifact_id="a1",
                memory_type=SessionMemoryType.OBSERVATION, scope=SessionMemoryScope.SESSION,
                creation_sequence=1, lifecycle=SessionMemoryLifecycle.ACTIVE,
                retrieval_key=key, provenance=("session-proof",))
    data.update(changes)
    return SessionMemoryRecord(**data)


def global_record(record_id="g1", key="risk", **changes):
    data = dict(namespace_type=GlobalMemoryNamespace.PROJECT, namespace_id="p1",
                global_record_id=record_id, record_version=1, source_session_id="session-1",
                source_phase8_record_ids=("s1",), source_artifact_ids=("a1",), source_phase="phase8",
                memory_type=GlobalMemoryType.VALIDATED_FACT, context_key=key, creation_sequence=1,
                lifecycle=GlobalMemoryLifecycle.ACTIVE, conflict_state=GlobalMemoryConflictState.CLEAR,
                provenance=("global-proof",), promotion_policy_id="explicit", retention_policy_id="bounded")
    data.update(changes)
    return GlobalContextRecord(**data)


def store(*records):
    return GlobalContextStore(records=records)
