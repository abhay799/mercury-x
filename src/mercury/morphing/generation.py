"""Deterministic bounded generation of registered morph profiles."""
from itertools import product
from mercury.morphing.contracts import MAX_MORPH_PROFILES,MorphAssignment,MorphGenerationMetadata,MorphPhaseResult,MorphPhaseStatus,MorphProfile,MorphProfileDraft,MorphProfileStatus,MorphValidationIssue,morph_profile_id
from mercury.morphing.requirements import StageMorphRequirementSet
from mercury.morphing.registry import ModelMorphCapabilityRegistry,canonical_morph_lineage_identity
def _draft(requirements,assignments):
 item=MorphProfileDraft(profile_id="sha256:"+"0"*64,composition_id=requirements.composition_id,precision_profile_id=requirements.precision_profile_id,assignments=assignments,provenance=("registered exact lineage variants enumerated deterministically",))
 return item.model_copy(update={"profile_id":morph_profile_id(item)})
def iter_morph_profile_drafts(requirements:StageMorphRequirementSet,registry:ModelMorphCapabilityRegistry):
 if not isinstance(requirements,StageMorphRequirementSet) or not isinstance(registry,ModelMorphCapabilityRegistry): raise ValueError("certified requirement set and registry required")
 options=[]
 for policy,identity in zip(requirements.requirements,requirements.stage_model_identities,strict=True):
  stage,provider,family,base,lineage,revision=identity
  variants=[x for x in registry.records if canonical_morph_lineage_identity(x)==(provider,family,base,lineage,revision) and not policy.morphing_forbidden and x.dimension not in policy.denied_dimensions and (not policy.allowed_dimensions or x.dimension in policy.allowed_dimensions)]
  options.append(tuple(sorted(variants,key=lambda x:(tuple(d.value for d in type(x.dimension)),x.variant_id))))
 if not options or any(not x for x in options): return
 for values in product(*options):
  assignments=tuple(MorphAssignment(stage_id=identity[0],provider=value.provider,family=value.family,base_model_id=value.base_model_id,lineage_id=value.lineage_id,source_revision=value.source_revision,variant_id=value.variant_id,dimension=value.dimension,hard_requirement_ids=policy.hard_requirement_ids,provenance=("exact registered variant",)) for policy,identity,value in zip(requirements.requirements,requirements.stage_model_identities,values,strict=True))
  yield _draft(requirements,assignments)
def generate_morph_profiles(requirements,registry,*,max_profiles=MAX_MORPH_PROFILES,morphing_required=True):
 if isinstance(max_profiles,bool) or not isinstance(max_profiles,int) or not 1<=max_profiles<=MAX_MORPH_PROFILES: raise ValueError("max_profiles must be within 1..128")
 drafts=[]; truncated=False
 for draft in iter_morph_profile_drafts(requirements,registry):
  if len(drafts)>=max_profiles: truncated=True; break
  drafts.append(draft)
 profiles=tuple(MorphProfile(**draft.model_dump(mode="python"),status=MorphProfileStatus.VALID,issues=()) for draft in drafts)
 issues=() if profiles or not morphing_required else (MorphValidationIssue(issue_id="no_valid_morph",violated_invariant="availability",reason="morphing required but no registered compatible variant exists"),)
 return MorphPhaseResult(status=MorphPhaseStatus.READY if profiles else (MorphPhaseStatus.FAIL if morphing_required else MorphPhaseStatus.NOT_APPLICABLE),valid_profiles=profiles,rejected_profiles=(),generation_metadata=MorphGenerationMetadata(max_profiles=max_profiles,emitted_valid_count=len(profiles),emitted_rejected_count=0,enumeration_completed=not truncated,truncated=truncated,lower_bound_unique_profiles=max_profiles+1 if truncated else len(profiles),canonical_order_description="stage order then canonical morph dimension order; reproducibility only"),issues=issues)
