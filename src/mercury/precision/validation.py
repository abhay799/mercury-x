"""Independent fail-closed validation of precision profile drafts."""
from __future__ import annotations
from mercury.precision.compatibility import evaluate_precision_compatibility
from mercury.precision.contracts import PrecisionEvidenceConstraint, PrecisionProfile, PrecisionProfileDraft, PrecisionProfileStatus, PrecisionValidationIssue, precision_profile_id
from mercury.precision.registry import ModelPrecisionCapabilityRegistry, lookup_exact_precision_capability
from mercury.precision.requirements import StagePrecisionRequirementSet

def validate_precision_profile(draft: PrecisionProfileDraft, requirement_set: StagePrecisionRequirementSet, registry: ModelPrecisionCapabilityRegistry, evidence_constraints: tuple[PrecisionEvidenceConstraint,...]=()) -> PrecisionProfile:
    if not isinstance(draft, PrecisionProfileDraft) or not isinstance(requirement_set, StagePrecisionRequirementSet) or not isinstance(registry, ModelPrecisionCapabilityRegistry): raise ValueError("validation requires certified Phase 6 contracts")
    issues=[]; requirements={item.stage_id:item for item in requirement_set.requirements}; assigned={item.stage_id:item for item in draft.assignments}
    if draft.composition_id != requirement_set.composition.composition_id: issues.append(PrecisionValidationIssue(issue_id="composition_identity",violated_invariant="composition_id",reason="draft composition identity must match requirements"))
    if set(assigned)!=set(requirements): issues.append(PrecisionValidationIssue(issue_id="stage_coverage",violated_invariant="assignments",reason="assignments must cover certified stages exactly once"))
    if draft.profile_id != precision_profile_id(draft): issues.append(PrecisionValidationIssue(issue_id="profile_id",violated_invariant="profile_id",reason="profile id must match canonical semantic content"))
    for stage, assignment in assigned.items():
        req=requirements.get(stage)
        cap=lookup_exact_precision_capability(registry,assignment.provider,assignment.model_id,assignment.family,assignment.revision)
        if req is None or cap is None:
            issues.append(PrecisionValidationIssue(issue_id="exact_capability",stage_id=stage,violated_invariant="capability",reason="exact stage requirement and capability must exist")); continue
        issues.extend(evaluate_precision_compatibility(cap,req,assignment,evidence_constraints).issues)
    issues=tuple(sorted({item.model_dump_json():item for item in issues}.values(),key=lambda i:i.model_dump_json()))
    return PrecisionProfile(**draft.model_dump(mode="python"),status=PrecisionProfileStatus.REJECTED if issues else PrecisionProfileStatus.VALID,issues=issues)
