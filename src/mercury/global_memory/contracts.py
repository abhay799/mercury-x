from enum import Enum
from hashlib import sha256
from json import dumps
from pydantic import Field,field_validator
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
class GlobalPromotionRequest(ContractModel): namespace_type:GlobalMemoryNamespace;namespace_id:str;source_phase8_record_ids:tuple[str,...];promotion_policy_id:str;retention_policy_id:str;memory_type:GlobalMemoryType;context_key:str;source_session_id:str;promotable:bool
class GlobalPromotionResult(ContractModel): status:GlobalMemoryPhaseStatus;record:GlobalContextRecord|None=None;reason:str|None=None
class GlobalMemoryQuery(ContractModel): namespace_type:GlobalMemoryNamespace;namespace_id:str;limit:int=Field(default=128,ge=1,le=128)
class GlobalMemoryRetrievalResult(ContractModel): status:GlobalMemoryPhaseStatus;records:tuple[GlobalContextRecord,...]
class GlobalConsolidationRequest(ContractModel): namespace_type:GlobalMemoryNamespace;namespace_id:str;source_record_ids:tuple[str,...];method_id:str;method_version:str;context_key:str;memory_type:GlobalMemoryType
class GlobalConsolidationResult(ContractModel): status:GlobalMemoryPhaseStatus;record:GlobalContextRecord|None=None
class GlobalGovernanceResult(ContractModel): status:GlobalMemoryPhaseStatus;reason:str|None=None
class GlobalMemoryLimitMetadata(ContractModel): max_records:int=Field(ge=1,le=4096);max_retrieval:int=Field(ge=1,le=128);max_promotion_sources:int=Field(ge=1,le=128);max_consolidation_inputs:int=Field(ge=1,le=256)
def canonical_global_context_payload(r): return {"namespace_type":r.namespace_type.value,"namespace_id":r.namespace_id,"record_version":r.record_version,"source_phase8_record_ids":sorted(r.source_phase8_record_ids),"source_artifact_ids":sorted(r.source_artifact_ids),"context_key":r.context_key}
def global_context_record_id(r): return "sha256:"+sha256(dumps(canonical_global_context_payload(r),sort_keys=True,separators=(",",":")).encode()).hexdigest()
