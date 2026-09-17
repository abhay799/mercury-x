from hashlib import sha256
from json import dumps
from mercury.contracts.base import ContractModel
from mercury.global_memory.contracts import GlobalContextRecord,GlobalMemoryNamespace,MAX_GLOBAL_RECORDS_PER_NAMESPACE,canonical_global_context_payload
class GlobalContextStore(ContractModel):
 records:tuple[GlobalContextRecord,...]=()
 def records_for_namespace(self,namespace_type,namespace_id):
  values=tuple(x for x in self.records if x.namespace_type is namespace_type and x.namespace_id==namespace_id)
  if not values: raise ValueError("cross-namespace or unknown access rejected")
  return values
 @property
 def fingerprint(self): return "sha256:"+sha256(dumps(sorted([canonical_global_context_payload(x) for x in self.records],key=str),sort_keys=True,separators=(",",":")).encode()).hexdigest()
def register_global_context_record(store,record,authorized_namespace_type,authorized_namespace_id):
 if not isinstance(store,GlobalContextStore) or not isinstance(record,GlobalContextRecord): raise ValueError("certified store and record required")
 if (record.namespace_type,record.namespace_id)!=(authorized_namespace_type,authorized_namespace_id): raise ValueError("namespace authorization mismatch")
 existing={x.global_record_id:x for x in store.records}
 if record.global_record_id in existing and existing[record.global_record_id]!=record: raise ValueError("conflicting duplicate identity")
 existing[record.global_record_id]=record
 if sum(x.namespace_type is record.namespace_type and x.namespace_id==record.namespace_id for x in existing.values())>MAX_GLOBAL_RECORDS_PER_NAMESPACE: raise ValueError("namespace cap exceeded")
 return GlobalContextStore(records=tuple(sorted(existing.values(),key=lambda x:(x.namespace_type.value,x.namespace_id,x.creation_sequence,x.global_record_id))))
