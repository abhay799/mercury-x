from hashlib import sha256
from json import dumps
from mercury.contracts.base import ContractModel
from mercury.morphing.contracts import ModelMorphCapability
from pydantic import field_validator
def canonical_morph_lineage_identity(record):
 if not isinstance(record,ModelMorphCapability): raise ValueError("record must be ModelMorphCapability")
 return record.provider,record.family,record.base_model_id,record.lineage_id,record.source_revision
class MorphRegistryIssue(ContractModel):
 issue_id:str; reason:str
 @field_validator("issue_id","reason")
 @classmethod
 def nonblank(cls,value):
  if not isinstance(value,str) or not value.strip(): raise ValueError("registry issue values must be nonblank")
  return value
class ModelMorphCapabilityRegistry(ContractModel):
 records:tuple[ModelMorphCapability,...]
 @field_validator("records")
 @classmethod
 def canonical_records(cls,values):
  by={}
  for record in values:
   if not isinstance(record,ModelMorphCapability): raise ValueError("records must contain ModelMorphCapability")
   key=(*canonical_morph_lineage_identity(record),record.variant_id,record.dimension)
   if key in by and by[key]!=record: raise ValueError("conflicting morph declarations share one exact identity")
   by[key]=record
  return tuple(by[key] for key in sorted(by,key=lambda item:tuple(str(x) for x in item)))
 @property
 def fingerprint(self): return "sha256:"+sha256(dumps([x.model_dump(mode="json") for x in sorted(self.records,key=lambda x:(canonical_morph_lineage_identity(x),x.variant_id,x.dimension.value))],sort_keys=True,separators=(",",":")).encode()).hexdigest()
def lookup_exact_morph_capability(registry,provider,family,base_model_id,lineage_id,source_revision):
 if not isinstance(registry,ModelMorphCapabilityRegistry): raise ValueError("registry required")
 key=(provider,family,base_model_id,lineage_id,source_revision)
 return next((x for x in registry.records if canonical_morph_lineage_identity(x)==key),None)
