from enum import Enum
from hashlib import sha256
from json import dumps
from mercury.contracts.base import ContractModel
from pydantic import field_validator,Field
MAX_SESSION_MEMORY_RECORDS=1024; MAX_RETRIEVED_RECORDS=64; MAX_COMPACTION_INPUT_RECORDS=128
class SessionMemoryType(str,Enum): OBSERVATION="OBSERVATION"; INTERMEDIATE_RESULT="INTERMEDIATE_RESULT"; TOOL_RESULT="TOOL_RESULT"; DECISION_CONTEXT="DECISION_CONTEXT"; EXECUTION_STATE="EXECUTION_STATE"; COMPACTED_SUMMARY="COMPACTED_SUMMARY"
class SessionMemoryScope(str,Enum): TURN="TURN"; TASK="TASK"; SESSION="SESSION"
class SessionMemoryLifecycle(str,Enum): ACTIVE="ACTIVE"; COMPACTED="COMPACTED"; EXPIRED="EXPIRED"; TOMBSTONED="TOMBSTONED"
class SessionMemoryPhaseStatus(str,Enum): READY="READY"; NOT_APPLICABLE="NOT_APPLICABLE"; FAIL="FAIL"
def _text(v):
 if not isinstance(v,str) or not v.strip(): raise ValueError("required value must be nonblank")
 return v
class SessionMemoryRecord(ContractModel):
 schema_version:str="mercury.session-memory/v1"; session_id:str; task_id:str; turn_id:str; record_id:str; record_version:int; source_phase:str; source_artifact_id:str; memory_type:SessionMemoryType; scope:SessionMemoryScope; creation_sequence:int; lifecycle:SessionMemoryLifecycle; retention_sequence:int|None=None; source_lineage_id:str|None=None; retrieval_key:str|None=None; provenance:tuple[str,...]
 @field_validator("session_id","task_id","turn_id","record_id","source_phase","source_artifact_id")
 @classmethod
 def ids(cls,v): return _text(v)
 @field_validator("record_version","creation_sequence")
 @classmethod
 def positive(cls,v):
  if isinstance(v,bool) or v<=0: raise ValueError("sequence and version must be positive")
  return v
 @field_validator("provenance")
 @classmethod
 def proof(cls,v):
  if not v or any(not x.strip() for x in v): raise ValueError("provenance required")
  return tuple(sorted(set(v)))
class SessionMemoryAdmissionRequest(ContractModel): record:SessionMemoryRecord
class SessionMemoryAdmissionResult(ContractModel): status:SessionMemoryPhaseStatus; record:SessionMemoryRecord|None=None; reason:str|None=None
class SessionMemoryQuery(ContractModel):
 session_id:str; limit:int=Field(default=MAX_RETRIEVED_RECORDS,ge=1,le=MAX_RETRIEVED_RECORDS); task_id:str|None=None; turn_id_min:str|None=None; turn_id_max:str|None=None; memory_types:tuple[SessionMemoryType,...]=(); scope:SessionMemoryScope|None=None; source_artifact_id:str|None=None; source_lineage_id:str|None=None; retrieval_key:str|None=None; lifecycle:SessionMemoryLifecycle|None=None
 @field_validator("session_id","task_id","turn_id_min","turn_id_max","source_artifact_id","source_lineage_id","retrieval_key")
 @classmethod
 def query_text(cls,v): return None if v is None else _text(v)
 @field_validator("memory_types")
 @classmethod
 def canonical_types(cls,v): return tuple(sorted(set(v),key=lambda x:x.value))
 @field_validator("turn_id_max")
 @classmethod
 def bounds(cls,v,info):
  lower=info.data.get("turn_id_min")
  if v is not None and lower is not None and lower>v: raise ValueError("turn_id_min must not exceed turn_id_max")
  return v
class SessionMemoryRetrievalResult(ContractModel): status:SessionMemoryPhaseStatus; records:tuple[SessionMemoryRecord,...]; provenance:tuple[str,...]=()
class SessionMemoryCompactionRequest(ContractModel): session_id:str; records:tuple[SessionMemoryRecord,...]
class SessionMemoryCompactionResult(ContractModel): status:SessionMemoryPhaseStatus; record:SessionMemoryRecord|None=None; reason:str|None=None
class SessionMemoryLifecycleResult(ContractModel): status:SessionMemoryPhaseStatus; record:SessionMemoryRecord|None=None; reason:str|None=None
class SessionMemoryLimitMetadata(ContractModel): max_records:int=Field(ge=1,le=MAX_SESSION_MEMORY_RECORDS); max_retrieved_records:int=Field(ge=1,le=MAX_RETRIEVED_RECORDS); max_compaction_input_records:int=Field(ge=1,le=MAX_COMPACTION_INPUT_RECORDS)
def canonical_session_memory_payload(record):
 return {"schema_version":record.schema_version,"session_id":record.session_id,"task_id":record.task_id,"turn_id":record.turn_id,"record_version":record.record_version,"source_phase":record.source_phase,"source_artifact_id":record.source_artifact_id,"memory_type":record.memory_type.value,"scope":record.scope.value,"creation_sequence":record.creation_sequence,"lifecycle":record.lifecycle.value}
def session_memory_record_id(record): return "sha256:"+sha256(dumps(canonical_session_memory_payload(record),sort_keys=True,separators=(",",":")).encode()).hexdigest()
