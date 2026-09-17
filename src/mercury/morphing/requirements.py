"""Explicit-policy, deterministic Phase 7 morph requirement derivation."""
from __future__ import annotations
from pydantic import field_validator,model_validator
from mercury.contracts.base import ContractModel
from mercury.morphing.contracts import MorphRequirement
def _nonblank(value,name):
 if not isinstance(value,str) or not value.strip(): raise ValueError(f"{name} must be nonblank")
 return value
class MorphRequirementDerivationRequest(ContractModel):
 composition_id:str; precision_profile_id:str; stage_model_identities:tuple[tuple[str,str,str,str,str,str],...]; explicit_requirements:tuple[MorphRequirement,...]=(); provenance:tuple[str,...]
 @model_validator(mode="after")
 def exact_stages(self):
  for value in (self.composition_id,self.precision_profile_id): _nonblank(value,"identity")
  stages={item[0] for item in self.stage_model_identities if len(item)==6 and all(isinstance(x,str) and x.strip() for x in item)}
  if not stages or any(item.stage_id not in stages for item in self.explicit_requirements): raise ValueError("explicit requirements must reference declared stages")
  return self
class StageMorphRequirementSet(ContractModel):
 composition_id:str; precision_profile_id:str; stage_model_identities:tuple[tuple[str,str,str,str,str,str],...]; requirements:tuple[MorphRequirement,...]; provenance:tuple[str,...]
class MorphRequirementDerivationResult(ContractModel): requirement_set:StageMorphRequirementSet; provenance:tuple[str,...]
def derive_morph_requirements(request:MorphRequirementDerivationRequest)->MorphRequirementDerivationResult:
 if not isinstance(request,MorphRequirementDerivationRequest): raise ValueError("request must be MorphRequirementDerivationRequest")
 explicit={item.stage_id:item for item in request.explicit_requirements}; reqs=[]
 for stage,*_ in request.stage_model_identities:
  reqs.append(explicit.get(stage) or MorphRequirement(requirement_id=f"morph:{request.composition_id}:{stage}",stage_id=stage,hard_requirement_ids=("certified-stage",),provenance=("derived from certified identity only",)))
 return MorphRequirementDerivationResult(requirement_set=StageMorphRequirementSet(composition_id=request.composition_id,precision_profile_id=request.precision_profile_id,stage_model_identities=tuple(sorted(request.stage_model_identities)),requirements=tuple(sorted(reqs,key=lambda x:x.stage_id)),provenance=("exact Phase 5 and Phase 6 identities preserved",)),provenance=("explicit policy only; no text or name inference",))
