from mercury.contracts.base import ContractModel
from mercury.morphing.contracts import ModelMorphCapability,MorphAssignment,MorphRequirement,MorphValidationIssue
class MorphCompatibilityResult(ContractModel): stage_id:str; compatible:bool; issues:tuple[MorphValidationIssue,...]; provenance:tuple[str,...]
def evaluate_morph_compatibility(capability:ModelMorphCapability,requirement:MorphRequirement,assignment:MorphAssignment,evidence_constraints=()):
 if not all(isinstance(x,t) for x,t in ((capability,ModelMorphCapability),(requirement,MorphRequirement),(assignment,MorphAssignment))): raise ValueError("certified morph contracts required")
 issues=[]
 if assignment.stage_id!=requirement.stage_id: issues.append("stage")
 if (assignment.provider,assignment.family,assignment.base_model_id,assignment.lineage_id,assignment.source_revision,assignment.variant_id,assignment.dimension)!=(capability.provider,capability.family,capability.base_model_id,capability.lineage_id,capability.source_revision,capability.variant_id,capability.dimension): issues.append("exact_variant")
 if requirement.morphing_forbidden or assignment.dimension in requirement.denied_dimensions or (requirement.allowed_dimensions and assignment.dimension not in requirement.allowed_dimensions): issues.append("policy")
 return MorphCompatibilityResult(stage_id=assignment.stage_id,compatible=not issues,issues=tuple(MorphValidationIssue(issue_id=x,violated_invariant=x,reason="exact registered lineage variant or explicit policy is incompatible") for x in sorted(issues)),provenance=("exact registered lineage/revision/variant evaluated",))
