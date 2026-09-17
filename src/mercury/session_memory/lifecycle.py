"""Exact-session immutable lifecycle transitions."""
from mercury.session_memory.contracts import SessionMemoryRecord,SessionMemoryLifecycle,SessionMemoryLifecycleResult,SessionMemoryPhaseStatus
_ALLOWED={(SessionMemoryLifecycle.ACTIVE,SessionMemoryLifecycle.COMPACTED),(SessionMemoryLifecycle.ACTIVE,SessionMemoryLifecycle.EXPIRED),(SessionMemoryLifecycle.ACTIVE,SessionMemoryLifecycle.TOMBSTONED),(SessionMemoryLifecycle.COMPACTED,SessionMemoryLifecycle.EXPIRED),(SessionMemoryLifecycle.COMPACTED,SessionMemoryLifecycle.TOMBSTONED)}
def transition_session_memory_lifecycle(record,target,authorized_session_id,store=None):
 if not isinstance(record,SessionMemoryRecord) or not isinstance(target,SessionMemoryLifecycle): raise ValueError("certified lifecycle contracts required")
 if record.session_id!=authorized_session_id: raise ValueError("cross-session lifecycle mutation rejected")
 if store is not None and store.is_session_closed(authorized_session_id): raise ValueError("closed session lifecycle mutation rejected")
 if (record.lifecycle,target) not in _ALLOWED: raise ValueError("invalid lifecycle transition")
 updated=record.model_copy(update={"lifecycle":target,"record_version":record.record_version+1})
 return SessionMemoryLifecycleResult(status=SessionMemoryPhaseStatus.READY,record=updated,reason="deterministic allowed lifecycle transition")
def expire_session_memory(record,authorized_session_id,store=None): return transition_session_memory_lifecycle(record,SessionMemoryLifecycle.EXPIRED,authorized_session_id,store)
def tombstone_session_memory(record,authorized_session_id,store=None): return transition_session_memory_lifecycle(record,SessionMemoryLifecycle.TOMBSTONED,authorized_session_id,store)
def close_session_memory(store,session_id,authorized_session_id,*,closure_sequence,policy_id):
 if session_id!=authorized_session_id: raise ValueError("cross-session closure rejected")
 records=tuple(transition_session_memory_lifecycle(x,SessionMemoryLifecycle.EXPIRED,session_id,store).record if x.session_id==session_id and x.lifecycle in (SessionMemoryLifecycle.ACTIVE,SessionMemoryLifecycle.COMPACTED) else x for x in store.records)
 return store.model_copy(update={"records":records}).close_session(session_id,closure_sequence=closure_sequence,policy_id=policy_id)
