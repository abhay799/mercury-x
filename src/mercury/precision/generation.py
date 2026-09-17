"""Bounded, deterministic enumeration of precision profiles."""
from __future__ import annotations
from itertools import product
from mercury.precision.compatibility import evaluate_precision_compatibility
from mercury.precision.contracts import MAX_PRECISION_PROFILES, PrecisionAssignment, PrecisionEvidenceConstraint, PrecisionGenerationMetadata, PrecisionMode, PrecisionPhaseResult, PrecisionPhaseStatus, PrecisionProfileDraft, PrecisionValidationIssue, precision_profile_id
from mercury.precision.registry import ModelPrecisionCapabilityRegistry, lookup_exact_precision_capability
from mercury.precision.requirements import StagePrecisionRequirementSet
from mercury.precision.validation import validate_precision_profile

def _draft(composition_id, assignments):
    placeholder="sha256:"+"0"*64
    item=PrecisionProfileDraft(profile_id=placeholder,composition_id=composition_id,assignments=assignments,provenance=("deterministic exact-registry enumeration",))
    return item.model_copy(update={"profile_id":precision_profile_id(item)})

def iter_precision_profile_drafts(requirement_set: StagePrecisionRequirementSet, registry: ModelPrecisionCapabilityRegistry, evidence_constraints: tuple[PrecisionEvidenceConstraint,...]=()):
    if not isinstance(requirement_set,StagePrecisionRequirementSet) or not isinstance(registry,ModelPrecisionCapabilityRegistry): raise ValueError("generation requires certified Phase 6 contracts")
    options=[]
    for requirement, identity in zip(requirement_set.requirements,requirement_set.stage_model_identities,strict=True):
        stage,provider,model_id,family,revision=identity; capability=lookup_exact_precision_capability(registry,provider,model_id,family,revision)
        choices=[]
        if capability:
            for mode in PrecisionMode:
                assignment=PrecisionAssignment(stage_id=stage,provider=provider,model_id=model_id,family=family,revision=revision,mode=mode,hard_requirement_ids=requirement.hard_requirement_ids,provenance=("certified stage identity",))
                if evaluate_precision_compatibility(capability,requirement,assignment,evidence_constraints).compatible: choices.append(assignment)
        options.append(tuple(choices))
    if not options or any(not item for item in options): return
    for assignments in product(*options): yield _draft(requirement_set.composition.composition_id,tuple(assignments))

def generate_precision_profiles(requirement_set: StagePrecisionRequirementSet, registry: ModelPrecisionCapabilityRegistry, evidence_constraints: tuple[PrecisionEvidenceConstraint,...]=(), *, max_profiles: int=MAX_PRECISION_PROFILES, adaptation_required: bool=True) -> PrecisionPhaseResult:
    if isinstance(max_profiles,bool) or not isinstance(max_profiles,int) or not 1<=max_profiles<=MAX_PRECISION_PROFILES: raise ValueError("max_profiles must be within the certified bound")
    drafts=[]; truncated=False
    for draft in iter_precision_profile_drafts(requirement_set,registry,evidence_constraints):
        if len(drafts)>=max_profiles: truncated=True; break
        drafts.append(draft)
    profiles=tuple(validate_precision_profile(item,requirement_set,registry,evidence_constraints) for item in drafts)
    valid=tuple(item for item in profiles if item.status.value=="VALID"); rejected=tuple(item for item in profiles if item.status.value=="REJECTED")
    issues=() if valid or rejected or not adaptation_required else (PrecisionValidationIssue(issue_id="no_valid_profile",violated_invariant="profile_availability",reason="adaptation is required but no exact compatible profile exists"),)
    status=PrecisionPhaseStatus.READY if valid else (PrecisionPhaseStatus.FAIL if adaptation_required else PrecisionPhaseStatus.NOT_APPLICABLE)
    metadata=PrecisionGenerationMetadata(max_profiles=max_profiles,emitted_valid_count=len(valid),emitted_rejected_count=len(rejected),enumeration_completed=not truncated,truncated=truncated,truncation_reason="first unique profile beyond cap observed" if truncated else None,lower_bound_unique_profiles=max_profiles+1 if truncated else len(profiles),canonical_order_description="stage order then FP32, BF16, FP16, INT8; reproducibility only")
    return PrecisionPhaseResult(status=status,valid_profiles=valid,rejected_profiles=rejected,generation_metadata=metadata,issues=issues)
