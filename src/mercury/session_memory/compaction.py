"""Deterministic, traceable structural session-memory compaction."""
from mercury.session_memory.contracts import *
def compact_session_memory(request,sources,authorized_session_id):
 if not isinstance(request,SessionMemoryCompactionRequest): raise ValueError("compaction request required")
 if request.session_id!=authorized_session_id or not sources or len(sources)>MAX_COMPACTION_INPUT_RECORDS: raise ValueError("session or source bounds invalid")
 by={}
 for source in sources:
  if not isinstance(source,SessionMemoryRecord) or source.session_id!=request.session_id or source.lifecycle is not SessionMemoryLifecycle.ACTIVE: raise ValueError("source is not eligible")
  if source.record_id in by and by[source.record_id]!=source: raise ValueError("conflicting source identity")
  by[source.record_id]=source
 ordered=tuple(by[x] for x in sorted(by))
 if tuple(x.record_id for x in ordered)!=request.source_record_ids: raise ValueError("request source identities must exactly match sources")
 if request.target_scope is SessionMemoryScope.TASK and any(x.task_id!=request.target_task_id for x in ordered): raise ValueError("cross-task compaction rejected")
 if request.target_scope is SessionMemoryScope.TURN and any(x.turn_id!=request.target_turn_id for x in ordered): raise ValueError("incompatible turn compaction rejected")
 payload="|".join((*request.source_record_ids,request.compaction_method_id,request.compaction_method_version,request.target_scope.value))
 record=SessionMemoryRecord(session_id=request.session_id,task_id=request.target_task_id or ordered[0].task_id,turn_id=request.target_turn_id or ordered[0].turn_id,record_id="sha256:"+__import__('hashlib').sha256(payload.encode()).hexdigest(),record_version=1,source_phase="phase8",source_artifact_id="compaction:"+request.compaction_method_id,memory_type=SessionMemoryType.COMPACTED_SUMMARY,scope=request.target_scope,creation_sequence=max(x.creation_sequence for x in ordered)+1,lifecycle=SessionMemoryLifecycle.COMPACTED,source_lineage_id="|".join(sorted(x.source_lineage_id or "" for x in ordered)),provenance=tuple(sorted({p for x in ordered for p in x.provenance})) or ("source provenance",))
 return SessionMemoryCompactionResult(status=SessionMemoryPhaseStatus.READY,record=record,source_record_ids=request.source_record_ids,source_record_versions=tuple(x.record_version for x in ordered),source_lineage_ids=tuple(x.source_lineage_id or "" for x in ordered),target_scope=request.target_scope,compaction_method_id=request.compaction_method_id,compaction_method_version=request.compaction_method_version)
