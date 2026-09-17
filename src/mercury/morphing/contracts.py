"""Immutable Phase 7 morph-profile contracts."""
from __future__ import annotations
from enum import Enum
from hashlib import sha256
from json import dumps
from typing import Literal
from pydantic import field_validator, model_validator
from mercury.contracts.base import ContractModel
MAX_MORPH_PROFILES=128
class MorphDimension(str,Enum): DEPTH="DEPTH"; WIDTH="WIDTH"; EXPERT="EXPERT"; ADAPTER="ADAPTER"; HEAD_CONTEXT="HEAD_CONTEXT"
class MorphProfileStatus(str,Enum): VALID="VALID"; REJECTED="REJECTED"
class MorphPhaseStatus(str,Enum): READY="READY"; NOT_APPLICABLE="NOT_APPLICABLE"; FAIL="FAIL"
def _text(v):
 if not isinstance(v,str) or not v.strip(): raise ValueError("value must be nonblank")
 return v
class MorphRequirement(ContractModel):
 requirement_id:str; stage_id:str; hard_requirement_ids:tuple[str,...]; morphing_forbidden:bool=False; allowed_dimensions:tuple[MorphDimension,...]=(); denied_dimensions:tuple[MorphDimension,...]=(); provenance:tuple[str,...]
 @field_validator("requirement_id","stage_id")
 @classmethod
 def text(cls,v): return _text(v)
class MorphEvidenceConstraint(ContractModel):
 constraint_id:str; stage_id:str; dimension:MorphDimension; requires_evidence:bool; evidence_ids:tuple[str,...]=(); provenance:tuple[str,...]
class ModelMorphCapability(ContractModel):
 provider:str; family:str; base_model_id:str; lineage_id:str; source_revision:str; variant_id:str; dimension:MorphDimension; provenance:tuple[str,...]
 @field_validator("provider","family","base_model_id","lineage_id","source_revision","variant_id")
 @classmethod
 def ident(cls,v): return _text(v)
class MorphAssignment(ContractModel):
 stage_id:str; provider:str; family:str; base_model_id:str; lineage_id:str; source_revision:str; variant_id:str; dimension:MorphDimension; hard_requirement_ids:tuple[str,...]; provenance:tuple[str,...]
class MorphProfileDraft(ContractModel):
 schema_version:Literal["mercury.morph-profile/v1"]="mercury.morph-profile/v1"; profile_id:str; composition_id:str; precision_profile_id:str; assignments:tuple[MorphAssignment,...]; provenance:tuple[str,...]
class MorphValidationIssue(ContractModel): issue_id:str; violated_invariant:str; reason:str
class MorphProfile(MorphProfileDraft):
 status:MorphProfileStatus; issues:tuple[MorphValidationIssue,...]
class MorphGenerationMetadata(ContractModel): max_profiles:int; emitted_valid_count:int; emitted_rejected_count:int; enumeration_completed:bool; truncated:bool; lower_bound_unique_profiles:int; canonical_order_description:str
class MorphPhaseResult(ContractModel): status:MorphPhaseStatus; valid_profiles:tuple[MorphProfile,...]; rejected_profiles:tuple[MorphProfile,...]; generation_metadata:MorphGenerationMetadata; issues:tuple[MorphValidationIssue,...]=()
def canonical_morph_profile_payload(profile:MorphProfileDraft|MorphProfile):
 return {"schema_version":profile.schema_version,"composition_id":profile.composition_id,"precision_profile_id":profile.precision_profile_id,"assignments":[{"stage_id":x.stage_id,"lineage":[x.provider,x.family,x.base_model_id,x.lineage_id,x.source_revision],"variant_id":x.variant_id,"dimension":x.dimension.value,"hard_requirement_ids":sorted(x.hard_requirement_ids)} for x in profile.assignments]}
def morph_profile_id(profile:MorphProfileDraft|MorphProfile): return "sha256:"+sha256(dumps(canonical_morph_profile_payload(profile),sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()).hexdigest()
