"""Deterministic trust assessment for declared model capability evidence."""

from __future__ import annotations

from enum import Enum

from pydantic import field_validator

from mercury.contracts.base import ContractModel


class CapabilityEvidenceKind(str, Enum):
    DECLARED = "declared"
    DOCUMENTED = "documented"
    MEASURED = "measured"
    OBSERVED = "observed"
    SIMULATED = "simulated"


class CapabilityEvidenceState(str, Enum):
    VALID = "valid"
    STALE = "stale"
    CONFLICTING = "conflicting"
    UNVERIFIED = "unverified"
    REVOKED = "revoked"


class EvidenceAssessmentStatus(str, Enum):
    ACCEPTABLE = "acceptable"
    INSUFFICIENT = "insufficient"
    CONFLICTING = "conflicting"
    STALE = "stale"
    UNVERIFIED = "unverified"


def _nonblank(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be nonblank")
    return value


class CapabilityEvidence(ContractModel):
    """One immutable source record supporting or contradicting one exact claim."""

    capability_claim: str
    source: str
    source_revision: str
    reference_id: str
    detail: str
    kind: CapabilityEvidenceKind
    state: CapabilityEvidenceState
    supports_claim: bool

    @field_validator(
        "capability_claim", "source", "source_revision", "reference_id", "detail"
    )
    @classmethod
    def required_text_is_nonblank(cls, value: str) -> str:
        return _nonblank(value, "evidence field")


class CapabilityEvidenceAssessmentRequirements(ContractModel):
    """Caller-supplied hard trust constraints for a single capability claim."""

    capability_claim: str
    requires_evidence: bool = False
    requires_current_valid: bool = False
    requires_measured_or_observed: bool = False
    requires_production_evidence: bool = False
    allow_simulated: bool = False
    reject_conflicts: bool = False

    @field_validator("capability_claim")
    @classmethod
    def capability_claim_is_nonblank(cls, value: str) -> str:
        return _nonblank(value, "capability_claim")


class CapabilityEvidenceIssue(ContractModel):
    issue_id: str
    reason: str

    @field_validator("issue_id", "reason")
    @classmethod
    def fields_are_nonblank(cls, value: str) -> str:
        return _nonblank(value, "evidence issue field")


class CapabilityEvidenceAssessment(ContractModel):
    """Categorical trust result with every original evidence record retained."""

    capability_claim: str
    requirements: CapabilityEvidenceAssessmentRequirements
    evidence: tuple[CapabilityEvidence, ...]
    status: EvidenceAssessmentStatus
    issues: tuple[CapabilityEvidenceIssue, ...]

    @field_validator("capability_claim")
    @classmethod
    def assessment_claim_is_nonblank(cls, value: str) -> str:
        return _nonblank(value, "capability_claim")

    @field_validator("evidence", mode="after")
    @classmethod
    def evidence_is_deterministic(
        cls, values: tuple[CapabilityEvidence, ...]
    ) -> tuple[CapabilityEvidence, ...]:
        if any(not isinstance(item, CapabilityEvidence) for item in values):
            raise ValueError("evidence must contain CapabilityEvidence values")
        return tuple(sorted(set(values), key=lambda item: (
            item.capability_claim, item.source, item.source_revision, item.reference_id,
            item.kind.value, item.state.value, item.supports_claim, item.detail,
        )))

    @field_validator("issues", mode="after")
    @classmethod
    def issues_are_deterministic(
        cls, values: tuple[CapabilityEvidenceIssue, ...]
    ) -> tuple[CapabilityEvidenceIssue, ...]:
        if any(not isinstance(item, CapabilityEvidenceIssue) for item in values):
            raise ValueError("issues must contain CapabilityEvidenceIssue values")
        return tuple(sorted(set(values), key=lambda item: (item.issue_id, item.reason)))


def _issue(issue_id: str, reason: str) -> CapabilityEvidenceIssue:
    return CapabilityEvidenceIssue(issue_id=issue_id, reason=reason)


def assess_capability_evidence(
    evidence: tuple[CapabilityEvidence, ...],
    requirements: CapabilityEvidenceAssessmentRequirements,
) -> CapabilityEvidenceAssessment:
    """Assess evidence for exactly one claim without assigning model preference."""

    if not isinstance(requirements, CapabilityEvidenceAssessmentRequirements):
        raise ValueError("requirements must be CapabilityEvidenceAssessmentRequirements")
    records = tuple(evidence)
    if any(not isinstance(item, CapabilityEvidence) for item in records):
        raise ValueError("evidence must contain CapabilityEvidence values")
    if any(item.capability_claim != requirements.capability_claim for item in records):
        raise ValueError("evidence capability claims must match assessment requirements")

    issues: list[CapabilityEvidenceIssue] = []
    valid_support = tuple(
        item for item in records
        if item.state is CapabilityEvidenceState.VALID and item.supports_claim
    )
    valid_negative = tuple(
        item for item in records
        if item.state is CapabilityEvidenceState.VALID and not item.supports_claim
    )
    has_conflict = bool(valid_support and valid_negative) or any(
        item.state is CapabilityEvidenceState.CONFLICTING for item in records
    )
    stale_only = bool(records) and all(
        item.state is CapabilityEvidenceState.STALE for item in records
    )
    unverified_only = bool(records) and all(
        item.state in (CapabilityEvidenceState.UNVERIFIED, CapabilityEvidenceState.REVOKED)
        for item in records
    )

    if has_conflict:
        issues.append(_issue("conflicting_evidence", "evidence contains unresolved conflicting capability claims"))
        status = EvidenceAssessmentStatus.CONFLICTING
    elif stale_only:
        issues.append(_issue("stale_evidence", "evidence is stale and remains explicitly stale"))
        status = EvidenceAssessmentStatus.STALE
    elif unverified_only:
        issues.append(_issue("unverified_evidence", "evidence is unverified or revoked"))
        status = EvidenceAssessmentStatus.UNVERIFIED
    elif not records:
        if requirements.requires_evidence:
            issues.append(_issue("missing_evidence", "hard evidence requirement has no supporting records"))
            status = EvidenceAssessmentStatus.INSUFFICIENT
        else:
            status = EvidenceAssessmentStatus.UNVERIFIED
    elif not valid_support:
        issues.append(_issue("missing_valid_support", "no valid evidence record supports the capability claim"))
        status = EvidenceAssessmentStatus.INSUFFICIENT
    elif requirements.requires_measured_or_observed and not any(
        item.kind in (CapabilityEvidenceKind.MEASURED, CapabilityEvidenceKind.OBSERVED)
        for item in valid_support
    ):
        issues.append(_issue("measured_evidence_required", "no valid measured or observed evidence supports the capability claim"))
        status = EvidenceAssessmentStatus.INSUFFICIENT
    elif requirements.requires_production_evidence and not any(
        item.kind is not CapabilityEvidenceKind.SIMULATED or requirements.allow_simulated
        for item in valid_support
    ):
        issues.append(_issue("production_evidence_required", "simulated-only evidence is not allowed for production evidence"))
        status = EvidenceAssessmentStatus.INSUFFICIENT
    else:
        status = EvidenceAssessmentStatus.ACCEPTABLE

    if requirements.requires_current_valid and not valid_support and status is EvidenceAssessmentStatus.ACCEPTABLE:
        issues.append(_issue("current_valid_evidence_required", "no current valid evidence supports the capability claim"))
        status = EvidenceAssessmentStatus.INSUFFICIENT

    return CapabilityEvidenceAssessment(
        capability_claim=requirements.capability_claim,
        requirements=requirements,
        evidence=records,
        status=status,
        issues=tuple(issues),
    )
