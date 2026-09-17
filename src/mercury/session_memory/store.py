from hashlib import sha256
from json import dumps
from mercury.contracts.base import ContractModel
from mercury.session_memory.contracts import SessionMemoryRecord,MAX_SESSION_MEMORY_RECORDS,canonical_session_memory_payload
class SessionMemoryStore(ContractModel):
 records:tuple[SessionMemoryRecord,...]=()
 def records_for_session(self,session_id):
  values=tuple(x for x in self.records if x.session_id==session_id)
  if not values: raise ValueError("cross-session or unknown session access rejected")
  return values
 @property
 def fingerprint(self): return "sha256:"+sha256(dumps([canonical_session_memory_payload(x) for x in self.records],sort_keys=True,separators=(",",":")).encode()).hexdigest()
def register_session_memory_record(store,record,active_session_id):
 if not isinstance(store,SessionMemoryStore) or not isinstance(record,SessionMemoryRecord): raise ValueError("certified store and record required")
 if record.session_id!=active_session_id: raise ValueError("cross-session write rejected")
 existing={x.record_id:x for x in store.records}
 if record.record_id in existing and existing[record.record_id]!=record: raise ValueError("conflicting duplicate identity")
 existing[record.record_id]=record
 if len(existing)>MAX_SESSION_MEMORY_RECORDS: raise ValueError("certified record cap exceeded")
 return SessionMemoryStore(records=tuple(sorted(existing.values(),key=lambda x:(x.session_id,x.creation_sequence,x.record_id))))
