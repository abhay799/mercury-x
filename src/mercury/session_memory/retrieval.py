"""Exact structured, session-isolated memory retrieval."""
from mercury.session_memory.contracts import SessionMemoryQuery,SessionMemoryRetrievalResult,SessionMemoryLifecycle
from mercury.session_memory.store import SessionMemoryStore
def retrieve_session_memory(query,store):
 if not isinstance(query,SessionMemoryQuery) or not isinstance(store,SessionMemoryStore): raise ValueError("certified query and store required")
 records=[]
 for record in store.records:
  if record.session_id!=query.session_id: continue
  if query.lifecycle is None:
   if record.lifecycle is not SessionMemoryLifecycle.ACTIVE: continue
  elif record.lifecycle is not query.lifecycle: continue
  if query.task_id is not None and record.task_id!=query.task_id: continue
  if query.turn_id_min is not None and record.turn_id<query.turn_id_min: continue
  if query.turn_id_max is not None and record.turn_id>query.turn_id_max: continue
  if query.memory_types and record.memory_type not in query.memory_types: continue
  if query.scope is not None and record.scope is not query.scope: continue
  if query.source_artifact_id is not None and record.source_artifact_id!=query.source_artifact_id: continue
  if query.source_lineage_id is not None and record.source_lineage_id!=query.source_lineage_id: continue
  if query.retrieval_key is not None and record.retrieval_key!=query.retrieval_key: continue
  records.append(record)
 records.sort(key=lambda x:(x.session_id,x.task_id,x.turn_id,x.creation_sequence,x.record_id))
 return SessionMemoryRetrievalResult(status=__import__('mercury.session_memory.contracts',fromlist=['SessionMemoryPhaseStatus']).SessionMemoryPhaseStatus.READY,records=tuple(records[:query.limit]),provenance=("exact structured filters and canonical order only",))
