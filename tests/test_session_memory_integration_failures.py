import pytest
from mercury.session_memory.contracts import *
from mercury.session_memory.admission import evaluate_memory_admission
from mercury.session_memory.store import SessionMemoryStore,register_session_memory_record
from mercury.session_memory.retrieval import retrieve_session_memory
from mercury.session_memory.lifecycle import expire_session_memory
def record(**u):
 v=dict(session_id="s",task_id="t",turn_id="u",record_id="sha256:"+"0"*64,record_version=1,source_phase="p",source_artifact_id="a",memory_type=SessionMemoryType.TOOL_RESULT,scope=SessionMemoryScope.SESSION,creation_sequence=1,lifecycle=SessionMemoryLifecycle.ACTIVE,provenance=("e",));v.update(u);return SessionMemoryRecord(**v)
def test_admission_store_retrieval_and_expiry_flow():
 source=record(); assert evaluate_memory_admission(source,"s",retainable=True).accepted
 store=register_session_memory_record(SessionMemoryStore(),source,"s")
 assert retrieve_session_memory(SessionMemoryQuery(session_id="s"),store).records==(source,)
 expired=expire_session_memory(source,"s").record
 assert retrieve_session_memory(SessionMemoryQuery(session_id="s"),SessionMemoryStore(records=(expired,))).records==()
def test_cross_session_and_secret_paths_fail_closed():
 assert not evaluate_memory_admission(record(),"other",retainable=True).accepted
 assert not evaluate_memory_admission(record(),"s",retainable=True,classification="token").accepted
 with pytest.raises(ValueError): register_session_memory_record(SessionMemoryStore(),record(),"other")
def test_closure_isolated_and_rejects_later_writes():
 closed=SessionMemoryStore().close_session("s",closure_sequence=1,policy_id="close")
 with pytest.raises(ValueError): register_session_memory_record(closed,record(),"s")
 assert not closed.is_session_closed("other")
