import pytest
from mercury.session_memory.contracts import SessionMemoryRecord,SessionMemoryType,SessionMemoryScope,SessionMemoryLifecycle
from mercury.session_memory.admission import evaluate_memory_admission
from mercury.session_memory.store import SessionMemoryStore,register_session_memory_record
def record(**u):
 v=dict(session_id="s",task_id="t",turn_id="u",record_id="sha256:"+"0"*64,record_version=1,source_phase="p",source_artifact_id="a",memory_type=SessionMemoryType.OBSERVATION,scope=SessionMemoryScope.SESSION,creation_sequence=1,lifecycle=SessionMemoryLifecycle.ACTIVE,provenance=("e",));v.update(u);return SessionMemoryRecord(**v)
def test_explicit_admission_and_session_partitioning():
 r=record(); assert evaluate_memory_admission(r,"s",retainable=True).accepted
 assert not evaluate_memory_admission(r,"other",retainable=True).accepted
 store=register_session_memory_record(SessionMemoryStore(),r,"s")
 assert store.records_for_session("s")== (r,)
 with pytest.raises(ValueError): store.records_for_session("other")
def test_nonretainable_and_explicit_secret_rejected():
 assert not evaluate_memory_admission(record(),"s",retainable=False).accepted
 assert not evaluate_memory_admission(record(),"s",retainable=True,classification="credential").accepted
def test_closed_session_is_exact_and_rejects_future_writes():
 store=SessionMemoryStore().close_session("s",closure_sequence=1,policy_id="close")
 assert store.is_session_closed("s") and not store.is_session_closed("other")
 with pytest.raises(ValueError): register_session_memory_record(store,record(),"s")
