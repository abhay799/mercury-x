"""Exact, deterministic precision compatibility checks."""
from __future__ import annotations
from pydantic import field_validator
from mercury.contracts.base import ContractModel
from mercury.precision.contracts import ModelPrecisionCapability, PrecisionAssignment, PrecisionEvidenceConstraint, PrecisionMode, PrecisionRequirement, PrecisionValidationIssue

class PrecisionCompatibilityResult(ContractModel):
    stage_id: str
    mode: PrecisionMode
    compatible: bool
    issues: tuple[PrecisionValidationIssue, ...] = ()
    provenance: tuple[str, ...]
    @field_validator("provenance")
    @classmethod
    def provenance_nonblank(cls, value):
        if not value or any(not item.strip() for item in value): raise ValueError("provenance must be nonblank")
        return tuple(sorted(set(value)))

def _issue(identifier: str, reason: str) -> PrecisionValidationIssue:
    return PrecisionValidationIssue(issue_id=identifier, violated_invariant=identifier, reason=reason)

def evaluate_precision_compatibility(capability: ModelPrecisionCapability, requirement: PrecisionRequirement, assignment: PrecisionAssignment, evidence_constraints: tuple[PrecisionEvidenceConstraint, ...] = ()) -> PrecisionCompatibilityResult:
    if not all(isinstance(item, expected) for item, expected in ((capability, ModelPrecisionCapability), (requirement, PrecisionRequirement), (assignment, PrecisionAssignment))): raise ValueError("compatibility requires Phase 6 contracts")
    issues=[]; mode=assignment.mode
    if assignment.stage_id != requirement.stage_id: issues.append(_issue("stage_identity", "assignment and requirement stage identities must match"))
    if (assignment.provider,assignment.model_id,assignment.family,assignment.revision) != (capability.provider,capability.model_id,capability.family,capability.revision): issues.append(_issue("model_identity", "assignment must preserve the exact capability revision"))
    if mode not in capability.supported_modes: issues.append(_issue("declared_support", "exact model revision does not explicitly support the assigned mode"))
    if mode in requirement.denied_modes: issues.append(_issue("denied_mode", "explicit hard policy denies the assigned mode"))
    if requirement.allowed_modes and mode not in requirement.allowed_modes: issues.append(_issue("allowed_mode", "assigned mode is not explicitly allowed"))
    if requirement.reduced_precision_forbidden and mode in (PrecisionMode.BF16,PrecisionMode.FP16,PrecisionMode.INT8): issues.append(_issue("reduced_precision", "reduced precision is explicitly forbidden"))
    if requirement.quantization_forbidden and mode is PrecisionMode.INT8: issues.append(_issue("quantization", "quantization is explicitly forbidden"))
    if requirement.fp16_forbidden and mode is PrecisionMode.FP16: issues.append(_issue("fp16_stability", "explicit stability policy forbids FP16"))
    if mode is PrecisionMode.INT8:
        matching=[item for item in evidence_constraints if item.stage_id==assignment.stage_id and item.mode is PrecisionMode.INT8 and item.requires_evidence and item.evidence_ids]
        if not matching: issues.append(_issue("int8_evidence", "INT8 requires explicit acceptable quantization evidence"))
    return PrecisionCompatibilityResult(stage_id=assignment.stage_id, mode=mode, compatible=not issues, issues=tuple(sorted(issues,key=lambda i:i.issue_id)), provenance=("exact model revision and explicit hard precision constraints evaluated",))
