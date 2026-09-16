import pytest
from pydantic import ValidationError

from mercury.models.evidence import (
    CapabilityEvidence,
    CapabilityEvidenceAssessmentRequirements,
    CapabilityEvidenceKind,
    CapabilityEvidenceState,
    EvidenceAssessmentStatus,
    assess_capability_evidence,
)


def evidence(kind: CapabilityEvidenceKind = CapabilityEvidenceKind.DECLARED, **changes: object) -> CapabilityEvidence:
    values: dict[str, object] = {
        "capability_claim": "tool_use", "source": "provider manifest", "source_revision": "v1",
        "reference_id": "manifest/tool-use", "detail": "declares function calling", "kind": kind,
        "state": CapabilityEvidenceState.VALID, "supports_claim": True,
    }
    values.update(changes)
    return CapabilityEvidence(**values)


def requirements(**changes: object) -> CapabilityEvidenceAssessmentRequirements:
    values: dict[str, object] = {"capability_claim": "tool_use"}
    values.update(changes)
    return CapabilityEvidenceAssessmentRequirements(**values)


@pytest.mark.parametrize("kind", list(CapabilityEvidenceKind))
def test_every_evidence_kind_is_preserved_distinctly(kind: CapabilityEvidenceKind) -> None:
    result = assess_capability_evidence((evidence(kind),), requirements())
    assert result.evidence[0].kind is kind
    assert result.status is EvidenceAssessmentStatus.ACCEPTABLE


def test_evidence_source_linkage_kind_and_state_are_strict() -> None:
    for field in ("capability_claim", "source", "source_revision", "reference_id", "detail"):
        with pytest.raises(ValidationError):
            evidence(**{field: " "})
    with pytest.raises(ValidationError):
        evidence(kind="unsupported")
    with pytest.raises(ValidationError):
        evidence(state="unsupported")


def test_missing_stale_and_unverified_evidence_are_categorically_fail_closed_when_required() -> None:
    hard = requirements(requires_evidence=True, requires_current_valid=True)
    assert assess_capability_evidence((), hard).status is EvidenceAssessmentStatus.INSUFFICIENT
    stale = assess_capability_evidence((evidence(state=CapabilityEvidenceState.STALE),), hard)
    assert stale.status is EvidenceAssessmentStatus.STALE
    assert stale.evidence[0].state is CapabilityEvidenceState.STALE
    assert assess_capability_evidence((evidence(state=CapabilityEvidenceState.UNVERIFIED),), hard).status is EvidenceAssessmentStatus.UNVERIFIED


def test_conflicts_are_preserved_and_fail_closed_when_requested() -> None:
    positive = evidence(reference_id="positive")
    negative = evidence(reference_id="negative", supports_claim=False)
    result = assess_capability_evidence((positive, negative), requirements(reject_conflicts=True))
    assert result.status is EvidenceAssessmentStatus.CONFLICTING
    assert result.evidence == (negative, positive)
    assert result.issues[0].reason.strip()


def test_measured_or_observed_and_production_evidence_requirements_are_explicit() -> None:
    measured = evidence(CapabilityEvidenceKind.MEASURED)
    observed = evidence(CapabilityEvidenceKind.OBSERVED)
    declared = evidence(CapabilityEvidenceKind.DECLARED)
    simulated = evidence(CapabilityEvidenceKind.SIMULATED)
    strict = requirements(requires_measured_or_observed=True)
    assert assess_capability_evidence((measured,), strict).status is EvidenceAssessmentStatus.ACCEPTABLE
    assert assess_capability_evidence((observed,), strict).status is EvidenceAssessmentStatus.ACCEPTABLE
    assert assess_capability_evidence((declared,), strict).status is EvidenceAssessmentStatus.INSUFFICIENT
    production = requirements(requires_production_evidence=True)
    assert assess_capability_evidence((simulated,), production).status is EvidenceAssessmentStatus.INSUFFICIENT
    assert assess_capability_evidence((simulated,), requirements(requires_production_evidence=True, allow_simulated=True)).status is EvidenceAssessmentStatus.ACCEPTABLE


def test_assessment_is_deterministic_immutable_and_does_not_expose_selection_fields() -> None:
    first, second = evidence(reference_id="b"), evidence(reference_id="a")
    left = assess_capability_evidence((first, second), requirements())
    right = assess_capability_evidence((second, first), requirements())
    assert left == right
    assert [item.reference_id for item in left.evidence] == ["a", "b"]
    with pytest.raises((AttributeError, TypeError, ValidationError)):
        left.evidence += ()
    forbidden = {"score", "rank", "winner", "selection", "preference", "graph_assignment", "hardware", "placement", "scheduler", "runtime"}
    assert not (forbidden & set(type(left).model_fields))
    with pytest.raises(ValueError):
        assess_capability_evidence((evidence(capability_claim="retrieval"),), requirements())
