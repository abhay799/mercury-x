from enum import Enum
from hashlib import sha256
from json import dumps
from pydantic import Field,field_validator,model_validator
from mercury.contracts.base import ContractModel
MAX_GLOBAL_RECORDS_PER_NAMESPACE=4096;MAX_GLOBAL_RETRIEVAL_RECORDS=128;MAX_PROMOTION_SOURCE_RECORDS=128;MAX_CONSOLIDATION_INPUT_RECORDS=256
class GlobalMemoryType(str,Enum): PROJECT_CONTEXT="PROJECT_CONTEXT";WORKSPACE_CONTEXT="WORKSPACE_CONTEXT";EXECUTION_KNOWLEDGE="EXECUTION_KNOWLEDGE";VALIDATED_FACT="VALIDATED_FACT";REUSABLE_ARTIFACT_CONTEXT="REUSABLE_ARTIFACT_CONTEXT";GLOBAL_SUMMARY="GLOBAL_SUMMARY"
class GlobalMemoryNamespace(str,Enum): TENANT="TENANT";WORKSPACE="WORKSPACE";PROJECT="PROJECT"
class GlobalMemoryLifecycle(str,Enum): ACTIVE="ACTIVE";SUPERSEDED="SUPERSEDED";EXPIRED="EXPIRED";REVOKED="REVOKED";TOMBSTONED="TOMBSTONED"
class GlobalMemoryConflictState(str,Enum): CLEAR="CLEAR";CONFLICTING="CONFLICTING"
class GlobalMemoryPhaseStatus(str,Enum): READY="READY";NOT_APPLICABLE="NOT_APPLICABLE";FAIL="FAIL"
def _text(v):
 if not isinstance(v,str) or not v.strip(): raise ValueError("nonblank required")
 return v
class GlobalContextRecord(ContractModel):
 namespace_type:GlobalMemoryNamespace;namespace_id:str;global_record_id:str;record_version:int;source_session_id:str;source_phase8_record_ids:tuple[str,...];source_artifact_ids:tuple[str,...];source_phase:str;memory_type:GlobalMemoryType;context_key:str;creation_sequence:int;lifecycle:GlobalMemoryLifecycle;conflict_state:GlobalMemoryConflictState;provenance:tuple[str,...];promotion_policy_id:str;retention_policy_id:str;supersedes_record_id:str|None=None;change_reason:str|None=None
 @field_validator("namespace_id","global_record_id","source_session_id","source_phase","context_key","promotion_policy_id","retention_policy_id")
 @classmethod
 def text(cls,v): return _text(v)
 @field_validator("record_version","creation_sequence")
 @classmethod
 def positive(cls,v):
  if not isinstance(v,int) or v<=0: raise ValueError("positive required")
  return v
class GlobalPromotionRequest(ContractModel):
 namespace_type:GlobalMemoryNamespace;namespace_id:str;authorized_namespace_type:GlobalMemoryNamespace;authorized_namespace_id:str;source_phase8_record_ids:tuple[str,...];promotion_policy_id:str;retention_policy_id:str;memory_type:GlobalMemoryType;context_key:str;source_session_id:str;promotable:bool
 @field_validator("namespace_id","authorized_namespace_id","promotion_policy_id","retention_policy_id","context_key","source_session_id")
 @classmethod
 def promotion_text(cls,v): return _text(v)
class GlobalPromotionResult(ContractModel): status:GlobalMemoryPhaseStatus;record:GlobalContextRecord|None=None;reason:str|None=None
class GlobalMemoryQuery(ContractModel):
 namespace_type:GlobalMemoryNamespace;namespace_id:str;authorized_namespace_type:GlobalMemoryNamespace;authorized_namespace_id:str;memory_types:tuple[GlobalMemoryType,...]|None=None;context_key:str|None=None;source_artifact_id:str|None=None;source_phase8_record_ids:tuple[str,...]|None=None;record_version:int|None=None;lifecycle:GlobalMemoryLifecycle|None=None;conflict_state:GlobalMemoryConflictState|None=None;current_only:bool=True;limit:int=Field(default=128,ge=1,le=128)
 @field_validator("namespace_id","authorized_namespace_id")
 @classmethod
 def query_text(cls,v): return _text(v)
 @field_validator("context_key","source_artifact_id")
 @classmethod
 def optional_query_text(cls,v): return None if v is None else _text(v)
 @field_validator("memory_types",mode="before")
 @classmethod
 def canonical_memory_types(cls,v):
  if v is None:return None
  if isinstance(v,(str,bytes,dict)):raise ValueError("memory types must be a collection")
  try:return tuple(sorted({GlobalMemoryType(item) for item in v},key=lambda item:item.value))
  except (TypeError,ValueError):raise ValueError("valid memory types required")
 @field_validator("source_phase8_record_ids",mode="before")
 @classmethod
 def canonical_source_record_ids(cls,v):
  if v is None:return None
  if isinstance(v,(str,bytes,dict)):raise ValueError("source record ids must be a collection")
  try:values=tuple(v)
  except TypeError:raise ValueError("source record ids must be a collection")
  if any(not isinstance(item,str) or not item.strip() for item in values):raise ValueError("nonblank source record ids required")
  if len(values)!=len(set(values)):raise ValueError("duplicate source record ids")
  return tuple(sorted(values))
 @field_validator("record_version")
 @classmethod
 def query_record_version(cls,v):
  if v is not None and (not isinstance(v,int) or isinstance(v,bool) or v<=0):raise ValueError("positive record version required")
  return v
 @field_validator("current_only")
 @classmethod
 def query_current_only(cls,v):
  if not isinstance(v,bool):raise ValueError("boolean current_only required")
  return v
class GlobalMemoryRetrievalResult(ContractModel): status:GlobalMemoryPhaseStatus;records:tuple[GlobalContextRecord,...]
class GlobalConsolidationRequest(ContractModel):
 namespace_type:GlobalMemoryNamespace;namespace_id:str;source_record_ids:tuple[str,...];method_id:str;method_version:str;context_key:str;memory_type:GlobalMemoryType
 @field_validator("namespace_id","method_id","method_version","context_key")
 @classmethod
 def consolidation_text(cls,v): return _text(v)
 @field_validator("source_record_ids",mode="before")
 @classmethod
 def canonical_consolidation_source_ids(cls,v):
  if isinstance(v,(str,bytes,dict)):raise ValueError("source record ids must be a collection")
  try:values=tuple(v)
  except TypeError:raise ValueError("source record ids must be a collection")
  if not values:raise ValueError("source record ids required")
  if any(not isinstance(item,str) or not item.strip() for item in values):raise ValueError("nonblank source record ids required")
  if len(values)!=len(set(values)):raise ValueError("duplicate source record ids")
  return tuple(sorted(values))
class GlobalConsolidationResult(ContractModel):
 status:GlobalMemoryPhaseStatus;record:GlobalContextRecord|None=None;namespace_type:GlobalMemoryNamespace;namespace_id:str;source_global_record_ids:tuple[str,...];source_record_versions:tuple[int,...];source_provenance:tuple[tuple[str,...],...];source_conflict_states:tuple[GlobalMemoryConflictState,...];consolidation_method_id:str;consolidation_method_version:str
 @field_validator("namespace_id","consolidation_method_id","consolidation_method_version")
 @classmethod
 def consolidation_result_text(cls,v): return _text(v)
 @model_validator(mode="before")
 @classmethod
 def canonical_traceability(cls,values):
  if not isinstance(values,dict):return values
  try:
   items=tuple(zip(values["source_global_record_ids"],values["source_record_versions"],values["source_provenance"],values["source_conflict_states"]))
   if len(items)==len(values["source_global_record_ids"])==len(values["source_record_versions"])==len(values["source_provenance"])==len(values["source_conflict_states"]):
    ordered=tuple(sorted(items,key=lambda item:item[0]))
    values=dict(values);values.update({"source_global_record_ids":tuple(item[0] for item in ordered),"source_record_versions":tuple(item[1] for item in ordered),"source_provenance":tuple(item[2] for item in ordered),"source_conflict_states":tuple(item[3] for item in ordered)})
  except (KeyError,TypeError):pass
  return values
 @model_validator(mode="after")
 def validate_traceability(self):
  items=tuple(zip(self.source_global_record_ids,self.source_record_versions,self.source_provenance,self.source_conflict_states))
  if not items:raise ValueError("source traceability required")
  if len(items)!=len(self.source_global_record_ids) or len(items)!=len(self.source_record_versions) or len(items)!=len(self.source_provenance) or len(items)!=len(self.source_conflict_states):raise ValueError("source traceability cardinality mismatch")
  if any(not isinstance(item[0],str) or not item[0].strip() for item in items):raise ValueError("nonblank source global record ids required")
  if len({item[0] for item in items})!=len(items):raise ValueError("duplicate source global record ids")
  if any(not isinstance(item[1],int) or isinstance(item[1],bool) or item[1]<=0 for item in items):raise ValueError("positive source record versions required")
  if any(not item[2] or any(not isinstance(evidence,str) or not evidence.strip() for evidence in item[2]) for item in items):raise ValueError("nonblank source provenance required")
  if self.record is not None and (self.record.namespace_type,self.record.namespace_id)!=(self.namespace_type,self.namespace_id):raise ValueError("record namespace mismatch")
  return self
class GlobalGovernanceResult(ContractModel): status:GlobalMemoryPhaseStatus;reason:str|None=None
class GlobalMemoryLimitMetadata(ContractModel): max_records:int=Field(ge=1,le=4096);max_retrieval:int=Field(ge=1,le=128);max_promotion_sources:int=Field(ge=1,le=128);max_consolidation_inputs:int=Field(ge=1,le=256)
def canonical_global_context_payload(r): return {"namespace_type":r.namespace_type.value,"namespace_id":r.namespace_id,"record_version":r.record_version,"source_phase8_record_ids":sorted(r.source_phase8_record_ids),"source_artifact_ids":sorted(r.source_artifact_ids),"context_key":r.context_key}
def global_context_record_id(r): return "sha256:"+sha256(dumps(canonical_global_context_payload(r),sort_keys=True,separators=(",",":")).encode()).hexdigest()
