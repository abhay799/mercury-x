import pytest
from mercury.session_memory.contracts import SessionMemoryType,SessionMemoryScope,SessionMemoryLifecycle,SessionMemoryPhaseStatus,MAX_SESSION_MEMORY_RECORDS,MAX_RETRIEVED_RECORDS,MAX_COMPACTION_INPUT_RECORDS,SessionMemoryRecord,session_memory_record_id
def record(**u):
 v=dict(session_id="session",task_id="task",turn_id="turn",record_id="sha256:"+"0"*64,record_version=1,source_phase="phase",source_artifact_id="artifact",memory_type=SessionMemoryType.OBSERVATION,scope=SessionMemoryScope.SESSION,creation_sequence=1,lifecycle=SessionMemoryLifecycle.ACTIVE,provenance=("evidence",));v.update(u);return SessionMemoryRecord(**v)
def test_locked_vocabularies_and_limits():
 assert tuple(x.value for x in SessionMemoryType)==("OBSERVATION","INTERMEDIATE_RESULT","TOOL_RESULT","DECISION_CONTEXT","EXECUTION_STATE","COMPACTED_SUMMARY")
 assert tuple(x.value for x in SessionMemoryScope)==("TURN","TASK","SESSION")
 assert tuple(x.value for x in SessionMemoryLifecycle)==("ACTIVE","COMPACTED","EXPIRED","TOMBSTONED")
 assert tuple(x.value for x in SessionMemoryPhaseStatus)==("READY","NOT_APPLICABLE","FAIL")
 assert (MAX_SESSION_MEMORY_RECORDS,MAX_RETRIEVED_RECORDS,MAX_COMPACTION_INPUT_RECORDS)==(1024,64,128)
def test_deterministic_identity_and_validation():
 a=record(); b=record(); assert session_memory_record_id(a)==session_memory_record_id(b)
 assert session_memory_record_id(record(session_id="other"))!=session_memory_record_id(a)
 with pytest.raises(Exception): record(session_id="")
 with pytest.raises(Exception): record(record_version=0)
 with pytest.raises(Exception): SessionMemoryScope("GLOBAL")
 with pytest.raises(Exception): a.session_id="changed"
