"""Immutable, deterministic contracts for Phase 6 adaptive precision."""

from __future__ import annotations

from enum import Enum
from hashlib import sha256
from json import dumps
import re
from typing import Final, Literal

from pydantic import Field, StrictInt, field_validator, model_validator

from mercury.contracts.base import ContractModel


PRECISION_SCHEMA_VERSION: Final[Literal["mercury.precision-profile/v1"]] = (
    "mercury.precision-profile/v1"
)
MAX_PRECISION_PROFILES: Final[int] = 128


class PrecisionMode(str, Enum):
    FP32 = "FP32"
    BF16 = "BF16"
    FP16 = "FP16"
    INT8 = "INT8"


class PrecisionProfileStatus(str, Enum):
    VALID = "VALID"
    REJECTED = "REJECTED"


class PrecisionPhaseStatus(str, Enum):
    READY = "READY"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    FAIL = "FAIL"


def _nonblank(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be nonblank")
    return value


def _canonical_strings(
    values: tuple[str, ...], field_name: str, *, required: bool = False
) -> tuple[str, ...]:
    if any(not isinstance(value, str) or not value.strip() for value in values):
        raise ValueError(f"{field_name} must contain nonblank values")
    normalized = tuple(sorted(set(values)))
    if required and not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return normalized


def _canonical_modes(
    values: tuple[PrecisionMode, ...], field_name: str, *, required: bool = False
) -> tuple[PrecisionMode, ...]:
    if any(not isinstance(value, PrecisionMode) for value in values):
        raise ValueError(f"{field_name} must contain PrecisionMode values")
    order = {mode: index for index, mode in enumerate(PrecisionMode)}
    normalized = tuple(sorted(set(values), key=order.__getitem__))
    if required and not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return normalized


def _sha256_id(value: str, field_name: str) -> str:
    if re.fullmatch(r"sha256:[0-9a-f]{64}", value) is None:
        raise ValueError(f"{field_name} must be a deterministic lowercase sha256 identifier")
    return value


class PrecisionRequirement(ContractModel):
    schema_version: Literal["mercury.precision-requirement/v1"] = (
        "mercury.precision-requirement/v1"
    )
    requirement_id: str
    stage_id: str
    hard_requirement_ids: tuple[str, ...]
    reduced_precision_forbidden: bool = False
    quantization_forbidden: bool = False
    fp16_forbidden: bool = False
    allowed_modes: tuple[PrecisionMode, ...] = ()
    denied_modes: tuple[PrecisionMode, ...] = ()
    provenance: tuple[str, ...]

    @field_validator("requirement_id", "stage_id")
    @classmethod
    def identities_are_nonblank(cls, value: str) -> str:
        return _nonblank(value, "precision requirement identity")

    @field_validator("hard_requirement_ids", "provenance", mode="after")
    @classmethod
    def string_collections_are_canonical(
        cls, values: tuple[str, ...], info: object
    ) -> tuple[str, ...]:
        return _canonical_strings(values, getattr(info, "field_name", "values"), required=True)

    @field_validator("allowed_modes", "denied_modes", mode="after")
    @classmethod
    def modes_are_canonical(
        cls, values: tuple[PrecisionMode, ...], info: object
    ) -> tuple[PrecisionMode, ...]:
        return _canonical_modes(values, getattr(info, "field_name", "modes"))


class PrecisionEvidenceConstraint(ContractModel):
    schema_version: Literal["mercury.precision-evidence-constraint/v1"] = (
        "mercury.precision-evidence-constraint/v1"
    )
    constraint_id: str
    stage_id: str
    mode: PrecisionMode
    requires_evidence: bool
    evidence_ids: tuple[str, ...] = ()
    provenance: tuple[str, ...]

    @field_validator("constraint_id", "stage_id")
    @classmethod
    def identities_are_nonblank(cls, value: str) -> str:
        return _nonblank(value, "precision evidence identity")

    @field_validator("evidence_ids", mode="after")
    @classmethod
    def evidence_ids_are_canonical(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _canonical_strings(values, "evidence_ids")

    @field_validator("provenance", mode="after")
    @classmethod
    def provenance_is_canonical(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _canonical_strings(values, "provenance", required=True)


class ModelPrecisionCapability(ContractModel):
    schema_version: Literal["mercury.model-precision-capability/v1"] = (
        "mercury.model-precision-capability/v1"
    )
    provider: str
    model_id: str
    family: str
    revision: str
    supported_modes: tuple[PrecisionMode, ...]
    evidence_ids: tuple[str, ...] = ()
    provenance: tuple[str, ...]

    @field_validator("provider", "model_id", "family", "revision")
    @classmethod
    def identity_is_nonblank(cls, value: str) -> str:
        return _nonblank(value, "model precision identity")

    @field_validator("supported_modes", mode="after")
    @classmethod
    def supported_modes_are_canonical(
        cls, values: tuple[PrecisionMode, ...]
    ) -> tuple[PrecisionMode, ...]:
        return _canonical_modes(values, "supported_modes", required=True)

    @field_validator("evidence_ids", mode="after")
    @classmethod
    def evidence_ids_are_canonical(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _canonical_strings(values, "evidence_ids")

    @field_validator("provenance", mode="after")
    @classmethod
    def provenance_is_canonical(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _canonical_strings(values, "provenance", required=True)


class PrecisionAssignment(ContractModel):
    stage_id: str
    provider: str
    model_id: str
    family: str
    revision: str
    mode: PrecisionMode
    hard_requirement_ids: tuple[str, ...]
    provenance: tuple[str, ...]

    @field_validator("stage_id", "provider", "model_id", "family", "revision")
    @classmethod
    def identities_are_nonblank(cls, value: str) -> str:
        return _nonblank(value, "precision assignment identity")

    @field_validator("hard_requirement_ids", "provenance", mode="after")
    @classmethod
    def strings_are_canonical(
        cls, values: tuple[str, ...], info: object
    ) -> tuple[str, ...]:
        return _canonical_strings(values, getattr(info, "field_name", "values"), required=True)


class PrecisionProfileDraft(ContractModel):
    schema_version: Literal["mercury.precision-profile/v1"] = PRECISION_SCHEMA_VERSION
    profile_id: str
    composition_id: str
    assignments: tuple[PrecisionAssignment, ...]
    provenance: tuple[str, ...]

    @field_validator("profile_id", "composition_id")
    @classmethod
    def ids_are_sha256(cls, value: str, info: object) -> str:
        return _sha256_id(value, getattr(info, "field_name", "profile id"))

    @field_validator("assignments", mode="after")
    @classmethod
    def assignments_are_ordered_and_unique(
        cls, values: tuple[PrecisionAssignment, ...]
    ) -> tuple[PrecisionAssignment, ...]:
        if not values:
            raise ValueError("assignments must not be empty")
        if any(not isinstance(value, PrecisionAssignment) for value in values):
            raise ValueError("assignments must contain PrecisionAssignment values")
        stage_ids = tuple(value.stage_id for value in values)
        if len(stage_ids) != len(set(stage_ids)):
            raise ValueError("assignment stage ids must be unique")
        return values

    @field_validator("provenance", mode="after")
    @classmethod
    def provenance_is_canonical(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _canonical_strings(values, "provenance", required=True)


class PrecisionValidationIssue(ContractModel):
    issue_id: str
    stage_id: str | None = None
    requirement_id: str | None = None
    violated_invariant: str
    reason: str

    @field_validator("issue_id", "violated_invariant", "reason")
    @classmethod
    def required_values_are_nonblank(cls, value: str) -> str:
        return _nonblank(value, "precision validation issue value")

    @field_validator("stage_id", "requirement_id")
    @classmethod
    def optional_values_are_nonblank(cls, value: str | None) -> str | None:
        return None if value is None else _nonblank(value, "precision validation reference")


class PrecisionProfile(PrecisionProfileDraft):
    status: PrecisionProfileStatus
    issues: tuple[PrecisionValidationIssue, ...]

    @field_validator("issues", mode="after")
    @classmethod
    def issues_are_canonical(
        cls, values: tuple[PrecisionValidationIssue, ...]
    ) -> tuple[PrecisionValidationIssue, ...]:
        if any(not isinstance(value, PrecisionValidationIssue) for value in values):
            raise ValueError("issues must contain PrecisionValidationIssue values")
        key = lambda value: (
            value.issue_id,
            value.stage_id or "",
            value.requirement_id or "",
            value.violated_invariant,
            value.reason,
        )
        return tuple(sorted({key(value): value for value in values}.values(), key=key))

    @model_validator(mode="after")
    def status_matches_issues(self) -> PrecisionProfile:
        if self.status is PrecisionProfileStatus.VALID and self.issues:
            raise ValueError("VALID precision profiles must not contain issues")
        if self.status is PrecisionProfileStatus.REJECTED and not self.issues:
            raise ValueError("REJECTED precision profiles require an issue")
        return self


class PrecisionGenerationMetadata(ContractModel):
    max_profiles: StrictInt = Field(ge=1, le=MAX_PRECISION_PROFILES)
    emitted_valid_count: StrictInt = Field(ge=0)
    emitted_rejected_count: StrictInt = Field(ge=0)
    enumeration_completed: bool
    truncated: bool
    truncation_reason: str | None = None
    lower_bound_unique_profiles: StrictInt = Field(ge=0)
    canonical_order_description: str

    @field_validator("canonical_order_description")
    @classmethod
    def description_is_nonblank(cls, value: str) -> str:
        return _nonblank(value, "canonical_order_description")

    @field_validator("truncation_reason")
    @classmethod
    def truncation_reason_is_nonblank_when_present(cls, value: str | None) -> str | None:
        return None if value is None else _nonblank(value, "truncation_reason")

    @model_validator(mode="after")
    def metadata_is_consistent(self) -> PrecisionGenerationMetadata:
        emitted = self.emitted_valid_count + self.emitted_rejected_count
        if emitted > self.max_profiles:
            raise ValueError("emitted profiles exceed max_profiles")
        if self.truncated:
            if self.enumeration_completed:
                raise ValueError("truncated enumeration cannot be completed")
            if self.truncation_reason is None:
                raise ValueError("truncated enumeration requires a reason")
            if self.lower_bound_unique_profiles <= self.max_profiles:
                raise ValueError("truncation requires a lower bound above max_profiles")
        else:
            if not self.enumeration_completed:
                raise ValueError("non-truncated enumeration must be completed")
            if self.truncation_reason is not None:
                raise ValueError("non-truncated enumeration cannot have a truncation reason")
            if self.lower_bound_unique_profiles != emitted:
                raise ValueError("completed enumeration lower bound must equal emitted count")
        return self


class PrecisionPhaseResult(ContractModel):
    status: PrecisionPhaseStatus
    valid_profiles: tuple[PrecisionProfile, ...]
    rejected_profiles: tuple[PrecisionProfile, ...]
    generation_metadata: PrecisionGenerationMetadata
    issues: tuple[PrecisionValidationIssue, ...] = ()

    @field_validator("valid_profiles", "rejected_profiles", mode="after")
    @classmethod
    def profiles_are_canonical(
        cls, values: tuple[PrecisionProfile, ...]
    ) -> tuple[PrecisionProfile, ...]:
        if any(type(value) is not PrecisionProfile for value in values):
            raise ValueError("final precision results require validated PrecisionProfile values")
        profile_ids = tuple(value.profile_id for value in values)
        if len(profile_ids) != len(set(profile_ids)):
            raise ValueError("profile ids must be unique")
        return tuple(sorted(values, key=lambda value: value.profile_id))

    @field_validator("issues", mode="after")
    @classmethod
    def issues_are_canonical(
        cls, values: tuple[PrecisionValidationIssue, ...]
    ) -> tuple[PrecisionValidationIssue, ...]:
        return PrecisionProfile.issues_are_canonical(values)

    @model_validator(mode="after")
    def result_is_consistent(self) -> PrecisionPhaseResult:
        if any(profile.status is not PrecisionProfileStatus.VALID for profile in self.valid_profiles):
            raise ValueError("valid_profiles must contain only VALID profiles")
        if any(profile.status is not PrecisionProfileStatus.REJECTED for profile in self.rejected_profiles):
            raise ValueError("rejected_profiles must contain only REJECTED profiles")
        profile_ids = tuple(
            profile.profile_id for profile in self.valid_profiles + self.rejected_profiles
        )
        if len(profile_ids) != len(set(profile_ids)):
            raise ValueError("profile ids must be unique across the phase result")
        if self.generation_metadata.emitted_valid_count != len(self.valid_profiles):
            raise ValueError("valid profile count does not match generation metadata")
        if self.generation_metadata.emitted_rejected_count != len(self.rejected_profiles):
            raise ValueError("rejected profile count does not match generation metadata")
        if self.status is PrecisionPhaseStatus.READY:
            if not self.valid_profiles:
                raise ValueError("READY requires at least one valid precision profile")
        elif self.status is PrecisionPhaseStatus.NOT_APPLICABLE:
            if self.valid_profiles or self.rejected_profiles or self.issues:
                raise ValueError("NOT_APPLICABLE cannot contain profiles or issues")
        elif self.status is PrecisionPhaseStatus.FAIL:
            if self.valid_profiles:
                raise ValueError("FAIL cannot contain valid precision profiles")
            if not self.rejected_profiles and not self.issues:
                raise ValueError("FAIL requires an explicit rejection or issue")
        return self


def canonical_precision_profile_payload(
    profile: PrecisionProfileDraft | PrecisionProfile,
) -> dict[str, object]:
    """Return profile semantics suitable for deterministic identity hashing."""
    if not isinstance(profile, PrecisionProfileDraft):
        raise ValueError("profile must be a PrecisionProfileDraft or PrecisionProfile")
    return {
        "schema_version": profile.schema_version,
        "composition_id": profile.composition_id,
        "assignments": [
            {
                "stage_id": assignment.stage_id,
                "model_identity": {
                    "provider": assignment.provider,
                    "model_id": assignment.model_id,
                    "family": assignment.family,
                    "revision": assignment.revision,
                },
                "mode": assignment.mode.value,
                "hard_requirement_ids": list(assignment.hard_requirement_ids),
            }
            for assignment in profile.assignments
        ],
    }


def precision_profile_id(profile: PrecisionProfileDraft | PrecisionProfile) -> str:
    """Return the deterministic SHA-256 identity for semantic profile content."""
    payload = canonical_precision_profile_payload(profile)
    canonical = dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return f"sha256:{sha256(canonical.encode('utf-8')).hexdigest()}"
