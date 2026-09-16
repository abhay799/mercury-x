from __future__ import annotations

import pytest
from pydantic import ValidationError

from mercury.precision.contracts import (
    MAX_PRECISION_PROFILES,
    ModelPrecisionCapability,
    PrecisionAssignment,
    PrecisionEvidenceConstraint,
    PrecisionGenerationMetadata,
    PrecisionMode,
    PrecisionPhaseResult,
    PrecisionPhaseStatus,
    PrecisionProfile,
    PrecisionProfileDraft,
    PrecisionProfileStatus,
    PrecisionRequirement,
    PrecisionValidationIssue,
    canonical_precision_profile_payload,
    precision_profile_id,
)


def assignment(
    stage_id: str = "stage-primary",
    mode: PrecisionMode = PrecisionMode.FP32,
    *,
    provenance: tuple[str, ...] = ("certified composition stage",),
    requirement_ids: tuple[str, ...] = ("requirement-primary",),
) -> PrecisionAssignment:
    return PrecisionAssignment(
        stage_id=stage_id,
        provider="provider-a",
        model_id="model-a",
        family="family-a",
        revision="revision-1",
        mode=mode,
        hard_requirement_ids=requirement_ids,
        provenance=provenance,
    )


def draft(
    assignments: tuple[PrecisionAssignment, ...] | None = None,
    *,
    provenance: tuple[str, ...] = ("certified Phase 5 composition",),
) -> PrecisionProfileDraft:
    candidate = PrecisionProfileDraft(
        profile_id="sha256:" + "0" * 64,
        composition_id="sha256:" + "1" * 64,
        assignments=assignments or (assignment(),),
        provenance=provenance,
    )
    return candidate.model_copy(update={"profile_id": precision_profile_id(candidate)})


def valid_profile(**changes: object) -> PrecisionProfile:
    values: dict[str, object] = {
        **draft().model_dump(mode="python"),
        "status": PrecisionProfileStatus.VALID,
        "issues": (),
    }
    values.update(changes)
    return PrecisionProfile(**values)


def metadata(**changes: object) -> PrecisionGenerationMetadata:
    values: dict[str, object] = {
        "max_profiles": MAX_PRECISION_PROFILES,
        "emitted_valid_count": 1,
        "emitted_rejected_count": 0,
        "enumeration_completed": True,
        "truncated": False,
        "truncation_reason": None,
        "lower_bound_unique_profiles": 1,
        "canonical_order_description": "certified stage order then canonical precision mode order",
    }
    values.update(changes)
    return PrecisionGenerationMetadata(**values)


def test_precision_mode_vocabulary_is_exact() -> None:
    assert tuple(item.value for item in PrecisionMode) == ("FP32", "BF16", "FP16", "INT8")


def test_precision_status_vocabularies_are_exact() -> None:
    assert tuple(item.value for item in PrecisionProfileStatus) == ("VALID", "REJECTED")
    assert tuple(item.value for item in PrecisionPhaseStatus) == (
        "READY",
        "NOT_APPLICABLE",
        "FAIL",
    )


def test_public_contracts_are_versioned_and_immutable() -> None:
    requirement = PrecisionRequirement(
        requirement_id="requirement-primary",
        stage_id="stage-primary",
        hard_requirement_ids=("upstream-requirement",),
        provenance=("explicit certified policy",),
    )
    constraint = PrecisionEvidenceConstraint(
        constraint_id="evidence-primary",
        stage_id="stage-primary",
        mode=PrecisionMode.INT8,
        requires_evidence=True,
        provenance=("explicit quantization evidence policy",),
    )
    capability = ModelPrecisionCapability(
        provider="provider-a",
        model_id="model-a",
        family="family-a",
        revision="revision-1",
        supported_modes=(PrecisionMode.INT8, PrecisionMode.FP32),
        provenance=("exact revision capability declaration",),
    )

    assert requirement.schema_version == "mercury.precision-requirement/v1"
    assert constraint.schema_version == "mercury.precision-evidence-constraint/v1"
    assert capability.schema_version == "mercury.model-precision-capability/v1"
    with pytest.raises(ValidationError):
        requirement.stage_id = "changed"  # type: ignore[misc]
    with pytest.raises(ValidationError):
        capability.supported_modes += (PrecisionMode.BF16,)  # type: ignore[misc]


@pytest.mark.parametrize(
    ("factory", "field"),
    (
        (lambda: assignment(), "stage_id"),
        (lambda: assignment(), "provider"),
        (lambda: PrecisionRequirement(requirement_id="requirement", stage_id="stage", hard_requirement_ids=("hard",), provenance=("source",)), "requirement_id"),
        (lambda: PrecisionEvidenceConstraint(constraint_id="constraint", stage_id="stage", mode=PrecisionMode.FP32, requires_evidence=False, provenance=("source",)), "constraint_id"),
        (lambda: ModelPrecisionCapability(provider="provider", model_id="model", family="family", revision="revision", supported_modes=(PrecisionMode.FP32,), provenance=("source",)), "revision"),
    ),
)
def test_required_identity_and_provenance_values_reject_blanks(factory, field: str) -> None:
    value = factory()
    values = value.model_dump(mode="python")
    values[field] = " "

    with pytest.raises(ValidationError):
        type(value)(**values)


def test_exact_model_identity_and_hard_requirements_are_preserved_canonically() -> None:
    value = assignment(
        requirement_ids=("requirement-b", "requirement-a", "requirement-a"),
        provenance=("source-b", "source-a", "source-a"),
    )

    assert (value.provider, value.model_id, value.family, value.revision) == (
        "provider-a",
        "model-a",
        "family-a",
        "revision-1",
    )
    assert value.hard_requirement_ids == ("requirement-a", "requirement-b")
    assert value.provenance == ("source-a", "source-b")


def test_duplicate_stage_assignments_fail_closed() -> None:
    duplicate = assignment()

    with pytest.raises(ValidationError, match="unique"):
        draft((duplicate, duplicate))


def test_equivalent_profile_payload_produces_same_sha256_id() -> None:
    first = draft(provenance=("source-b", "source-a"))
    second = draft(provenance=("source-a", "source-b"))

    assert canonical_precision_profile_payload(first) == canonical_precision_profile_payload(second)
    assert precision_profile_id(first) == precision_profile_id(second)
    assert precision_profile_id(first).startswith("sha256:")


def test_profile_id_changes_for_semantic_identity_or_precision_changes() -> None:
    first = draft()
    different_mode = draft((assignment(mode=PrecisionMode.BF16),))
    different_revision = draft(
        (assignment().model_copy(update={"revision": "revision-2"}),)
    )

    assert precision_profile_id(first) != precision_profile_id(different_mode)
    assert precision_profile_id(first) != precision_profile_id(different_revision)


def test_profile_id_payload_preserves_declared_stage_order() -> None:
    first = draft((assignment("stage-a"), assignment("stage-b", PrecisionMode.BF16)))
    second = draft((assignment("stage-b", PrecisionMode.BF16), assignment("stage-a")))

    assert canonical_precision_profile_payload(first)["assignments"][0]["stage_id"] == "stage-a"
    assert precision_profile_id(first) != precision_profile_id(second)


def test_profile_status_requires_consistent_issues() -> None:
    issue = PrecisionValidationIssue(
        issue_id="unsupported_mode",
        violated_invariant="capability_support",
        reason="exact model revision does not declare support",
    )
    rejected = valid_profile(status=PrecisionProfileStatus.REJECTED, issues=(issue,))

    assert rejected.status is PrecisionProfileStatus.REJECTED
    with pytest.raises(ValidationError):
        valid_profile(issues=(issue,))
    with pytest.raises(ValidationError):
        valid_profile(status=PrecisionProfileStatus.REJECTED, issues=())


def test_generation_metadata_enforces_certified_bound_and_transparency() -> None:
    assert metadata().max_profiles == 128
    truncated = metadata(
        max_profiles=2,
        emitted_valid_count=2,
        enumeration_completed=False,
        truncated=True,
        truncation_reason="first unique profile beyond the configured cap was observed",
        lower_bound_unique_profiles=3,
    )

    assert truncated.truncated is True
    with pytest.raises(ValidationError):
        metadata(max_profiles=129)
    with pytest.raises(ValidationError):
        metadata(max_profiles=0)
    with pytest.raises(ValidationError):
        metadata(truncated=True, enumeration_completed=True)


def test_phase_result_statuses_are_fail_closed_and_candidate_sets_are_separate() -> None:
    valid = valid_profile()
    ready = PrecisionPhaseResult(
        status=PrecisionPhaseStatus.READY,
        valid_profiles=(valid,),
        rejected_profiles=(),
        generation_metadata=metadata(),
    )
    not_applicable = PrecisionPhaseResult(
        status=PrecisionPhaseStatus.NOT_APPLICABLE,
        valid_profiles=(),
        rejected_profiles=(),
        generation_metadata=metadata(emitted_valid_count=0, lower_bound_unique_profiles=0),
    )

    assert ready.status is PrecisionPhaseStatus.READY
    assert not_applicable.status is PrecisionPhaseStatus.NOT_APPLICABLE
    with pytest.raises(ValidationError):
        PrecisionPhaseResult(
            status=PrecisionPhaseStatus.FAIL,
            valid_profiles=(valid,),
            rejected_profiles=(),
            generation_metadata=metadata(),
        )


def test_contract_collections_are_immutable() -> None:
    profile = valid_profile()

    assert isinstance(profile.assignments, tuple)
    with pytest.raises(TypeError):
        profile.assignments[0] = profile.assignments[0]  # type: ignore[index]
    with pytest.raises(ValidationError):
        profile.assignments[0].stage_id = "changed"  # type: ignore[misc]


def test_contracts_expose_no_forbidden_phase6_decisions() -> None:
    forbidden = {
        "rank", "score", "winner", "best_profile", "preferred_precision",
        "fallback", "selected_model", "hardware", "device", "placement",
        "scheduler", "runtime", "cost", "latency", "quality_optimization",
    }
    contracts = (
        PrecisionRequirement,
        PrecisionEvidenceConstraint,
        ModelPrecisionCapability,
        PrecisionAssignment,
        PrecisionProfileDraft,
        PrecisionProfile,
        PrecisionValidationIssue,
        PrecisionGenerationMetadata,
        PrecisionPhaseResult,
    )

    for contract in contracts:
        assert forbidden.isdisjoint(contract.model_fields)
