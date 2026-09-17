from mercury.session_memory.contracts import *
from mercury.session_memory.compaction import compact_session_memory
def record(**u):
 v=dict(session_id="s",task_id="t",turn_id="u",record_id="sha256:"+"0"*64,record_version=1,source_phase="p",source_artifact_id="a",memory_type=SessionMemoryType.OBSERVATION,scope=SessionMemoryScope.TASK,creation_sequence=1,lifecycle=SessionMemoryLifecycle.ACTIVE,source_lineage_id="lineage",provenance=("e",));v.update(u);return SessionMemoryRecord(**v)
def request(ids): return SessionMemoryCompactionRequest(session_id="s",source_record_ids=ids,target_scope=SessionMemoryScope.TASK,target_task_id="t",compaction_method_id="method",compaction_method_version="v1")
def test_compaction_preserves_traceability_deterministically():
 a=record(); result=compact_session_memory(request((a.record_id,)),(a,),"s")
 assert result.record.memory_type is SessionMemoryType.COMPACTED_SUMMARY and result.source_record_ids==(a.record_id,) and result.source_lineage_ids==("lineage",)
def test_expired_and_cross_session_sources_fail_closed():
 a=record(lifecycle=SessionMemoryLifecycle.EXPIRED)
 try: compact_session_memory(request((a.record_id,)),(a,),"s")
 except ValueError: pass
 else: assert False
