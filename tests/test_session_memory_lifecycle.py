import pytest
from mercury.session_memory.contracts import *
from mercury.session_memory.lifecycle import transition_session_memory_lifecycle,expire_session_memory,tombstone_session_memory
def record(**u):
 v=dict(session_id="s",task_id="t",turn_id="u",record_id="sha256:"+"0"*64,record_version=1,source_phase="p",source_artifact_id="a",memory_type=SessionMemoryType.OBSERVATION,scope=SessionMemoryScope.SESSION,creation_sequence=1,lifecycle=SessionMemoryLifecycle.ACTIVE,provenance=("e",));v.update(u);return SessionMemoryRecord(**v)
def test_allowed_transition_is_immutable_and_versioned():
 source=record(); result=transition_session_memory_lifecycle(source,SessionMemoryLifecycle.COMPACTED,"s")
 assert result.record.lifecycle is SessionMemoryLifecycle.COMPACTED and result.record.record_version==2 and source.lifecycle is SessionMemoryLifecycle.ACTIVE
def test_expiry_tombstone_and_cross_session_fail_closed():
 assert expire_session_memory(record(),"s").record.lifecycle is SessionMemoryLifecycle.EXPIRED
 assert tombstone_session_memory(record(),"s").record.lifecycle is SessionMemoryLifecycle.TOMBSTONED
 with pytest.raises(ValueError): transition_session_memory_lifecycle(record(),SessionMemoryLifecycle.EXPIRED,"other")
