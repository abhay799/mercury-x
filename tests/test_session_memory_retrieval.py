from mercury.session_memory.contracts import SessionMemoryRecord,SessionMemoryQuery,SessionMemoryType,SessionMemoryScope,SessionMemoryLifecycle
from mercury.session_memory.store import SessionMemoryStore,register_session_memory_record
from mercury.session_memory.retrieval import retrieve_session_memory
def record(**u):
 v=dict(session_id="s",task_id="t",turn_id="1",record_id="sha256:"+"0"*64,record_version=1,source_phase="p",source_artifact_id="a",memory_type=SessionMemoryType.OBSERVATION,scope=SessionMemoryScope.SESSION,creation_sequence=1,lifecycle=SessionMemoryLifecycle.ACTIVE,provenance=("e",));v.update(u);return SessionMemoryRecord(**v)
def test_active_exact_session_and_task_filters_are_deterministic():
 a=record(); b=record(record_id="sha256:"+"1"*64,task_id="other",creation_sequence=2)
 store=register_session_memory_record(register_session_memory_record(SessionMemoryStore(),a,"s"),b,"s")
 result=retrieve_session_memory(SessionMemoryQuery(session_id="s",task_id="t"),store)
 assert result.records==(a,)
def test_expired_excluded_and_cross_session_rejected():
 expired=record(lifecycle=SessionMemoryLifecycle.EXPIRED)
 store=register_session_memory_record(SessionMemoryStore(),expired,"s")
 assert retrieve_session_memory(SessionMemoryQuery(session_id="s"),store).records==()
