from hashlib import sha256
from json import dumps
from mercury.contracts.base import ContractModel
from mercury.session_memory.contracts import SessionMemoryRecord,MAX_SESSION_MEMORY_RECORDS,canonical_session_memory_payload
class SessionMemoryStore(ContractModel):
 records:tuple[SessionMemoryRecord,...]=()
 closed_sessions:tuple[tuple[str,int,str],...]=()
 def close_session(self,session_id,*,closure_sequence,policy_id):
  if not isinstance(session_id,str) or not session_id.strip() or not isinstance(closure_sequence,int) or closure_sequence<=0 or not isinstance(policy_id,str) or not policy_id.strip(): raise ValueError("malformed closure metadata")
  values={item[0]:item for item in self.closed_sessions}; existing=values.get(session_id); proposed=(session_id,closure_sequence,policy_id)
  if existing is not None and existing!=proposed: raise ValueError("conflicting closure metadata")
  values[session_id]=proposed
  return SessionMemoryStore(records=self.records,closed_sessions=tuple(values[key] for key in sorted(values)))
 def is_session_closed(self,session_id): return any(item[0]==session_id for item in self.closed_sessions)
 def get_session_closure_metadata(self,session_id): return next((item for item in self.closed_sessions if item[0]==session_id),None)
 def records_for_session(self,session_id):
  values=tuple(x for x in self.records if x.session_id==session_id)
  if not values: raise ValueError("cross-session or unknown session access rejected")
  return values
 @property
 def fingerprint(self): return "sha256:"+sha256(dumps({"records":[canonical_session_memory_payload(x) for x in self.records],"closed_sessions":self.closed_sessions},sort_keys=True,separators=(",",":")).encode()).hexdigest()
def register_session_memory_record(store,record,active_session_id):
 if not isinstance(store,SessionMemoryStore) or not isinstance(record,SessionMemoryRecord): raise ValueError("certified store and record required")
 if record.session_id!=active_session_id: raise ValueError("cross-session write rejected")
 if store.is_session_closed(active_session_id): raise ValueError("closed session rejects writes")
 existing={x.record_id:x for x in store.records}
 if record.record_id in existing and existing[record.record_id]!=record: raise ValueError("conflicting duplicate identity")
 existing[record.record_id]=record
 if len(existing)>MAX_SESSION_MEMORY_RECORDS: raise ValueError("certified record cap exceeded")
 return SessionMemoryStore(records=tuple(sorted(existing.values(),key=lambda x:(x.session_id,x.creation_sequence,x.record_id))),closed_sessions=store.closed_sessions)
