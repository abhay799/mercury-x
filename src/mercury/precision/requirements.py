"""Deterministic derivation of explicit Phase 6 precision requirements."""

from __future__ import annotations

from typing import Literal

from pydantic import field_validator, model_validator

from mercury.composition.contracts import CompositionCandidate, CompositionValidity
from mercury.contracts.base import ContractModel
from mercury.precision.contracts import PrecisionMode, PrecisionRequirement


def _nonblank(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be nonblank")
    return value


def _identity(node: object) -> tuple[str, str, str, str, str]:
    stage_id = _nonblank(getattr(node, "stage_id", None), "stage_id")
    record = getattr(node, "model_record", None)
    return (
        stage_id,
        _nonblank(getattr(record, "provider", None), "provider"),
        _nonblank(getattr(record, "model_id", None), "model_id"),
        _nonblank(getattr(record, "family", None), "family"),
        _nonblank(getattr(record, "revision", None), "revision"),
    )


class PrecisionRequirementDerivationRequest(ContractModel):
    """A certified candidate plus explicit, stage-scoped precision policy."""

    composition: CompositionCandidate
    explicit_requirements: tuple[PrecisionRequirement, ...] = ()

    @field_validator("explicit_requirements", mode="after")
    @classmethod
    def requirements_are_canonical(
        cls, values: tuple[PrecisionRequirement, ...]
    ) -> tuple[PrecisionRequirement, ...]:
        if any(not isinstance(item, PrecisionRequirement) for item in values):
            raise ValueError("explicit_requirements must contain PrecisionRequirement values")
        by_stage = {item.stage_id: item for item in values}
        if len(by_stage) != len(values):
            raise ValueError("explicit requirements may contain only one policy per stage")
        return tuple(by_stage[key] for key in sorted(by_stage))

    @model_validator(mode="after")
    def requires_a_valid_certified_composition(self) -> PrecisionRequirementDerivationRequest:
        if not isinstance(self.composition, CompositionCandidate):
            raise ValueError("composition must be a certified CompositionCandidate")
        if self.composition.validity is not CompositionValidity.VALID:
            raise ValueError("precision derivation requires a valid certified composition")
        identities = tuple(_identity(node) for node in self.composition.nodes)
        stage_ids = tuple(identity[0] for identity in identities)
        if not stage_ids or len(stage_ids) != len(set(stage_ids)):
            raise ValueError("composition stages must be nonempty and unique")
        unknown = {item.stage_id for item in self.explicit_requirements}.difference(stage_ids)
        if unknown:
            raise ValueError("explicit precision requirement references an undeclared composition stage")
        return self


class StagePrecisionRequirementSet(ContractModel):
    """Per-stage hard precision constraints tied to one certified composition."""

    schema_version: Literal["mercury.stage-precision-requirements/v1"] = (
        "mercury.stage-precision-requirements/v1"
    )
    composition: CompositionCandidate
    requirements: tuple[PrecisionRequirement, ...]
    stage_model_identities: tuple[tuple[str, str, str, str, str], ...]
    provenance: tuple[str, ...]

    @field_validator("requirements", mode="after")
    @classmethod
    def requirements_are_canonical(
        cls, values: tuple[PrecisionRequirement, ...]
    ) -> tuple[PrecisionRequirement, ...]:
        if not values or any(not isinstance(item, PrecisionRequirement) for item in values):
            raise ValueError("requirements must contain precision requirements")
        by_stage = {item.stage_id: item for item in values}
        if len(by_stage) != len(values):
            raise ValueError("stage precision requirements must be unique")
        return tuple(by_stage[key] for key in sorted(by_stage))

    @field_validator("stage_model_identities", mode="after")
    @classmethod
    def identities_are_exact_and_nonblank(
        cls, values: tuple[tuple[str, str, str, str, str], ...]
    ) -> tuple[tuple[str, str, str, str, str], ...]:
        if not values:
            raise ValueError("stage_model_identities must not be empty")
        for identity in values:
            if len(identity) != 5:
                raise ValueError("stage model identity must contain stage/provider/model/family/revision")
            for item in identity:
                _nonblank(item, "stage model identity")
        if len({item[0] for item in values}) != len(values):
            raise ValueError("stage model identities must be unique")
        return tuple(sorted(values, key=lambda item: item[0]))

    @field_validator("provenance", mode="after")
    @classmethod
    def provenance_is_canonical(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if any(not isinstance(item, str) or not item.strip() for item in values):
            raise ValueError("provenance must contain nonblank values")
        normalized = tuple(sorted(set(values)))
        if not normalized:
            raise ValueError("provenance must not be empty")
        return normalized

    @model_validator(mode="after")
    def preserves_certified_identity(self) -> StagePrecisionRequirementSet:
        if self.composition.validity is not CompositionValidity.VALID:
            raise ValueError("requirement sets require a valid certified composition")
        identities = tuple(_identity(node) for node in self.composition.nodes)
        if self.stage_model_identities != tuple(sorted(identities, key=lambda item: item[0])):
            raise ValueError("stage model identities must exactly preserve the composition")
        if {item.stage_id for item in self.requirements} != {item[0] for item in identities}:
            raise ValueError("requirements must cover each certified composition stage exactly once")
        return self


class PrecisionRequirementDerivationResult(ContractModel):
    """Immutable trace of a successful explicit-policy derivation."""

    requirement_set: StagePrecisionRequirementSet
    provenance: tuple[str, ...]

    @field_validator("provenance", mode="after")
    @classmethod
    def provenance_is_nonblank(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if any(not isinstance(item, str) or not item.strip() for item in values):
            raise ValueError("derivation provenance must contain nonblank values")
        normalized = tuple(sorted(set(values)))
        if not normalized:
            raise ValueError("derivation provenance must not be empty")
        return normalized


def _derived_requirement(
    composition: CompositionCandidate, node: object, explicit: PrecisionRequirement | None
) -> PrecisionRequirement:
    stage_id = _identity(node)[0]
    if explicit is None:
        return PrecisionRequirement(
            requirement_id=f"precision:{composition.composition_id}:{stage_id}",
            stage_id=stage_id,
            hard_requirement_ids=composition.satisfied_requirement_ids,
            provenance=(
                "derived solely from certified Phase 5 stage identity and declared hard requirements",
            ),
        )
    denied = set(explicit.denied_modes)
    if explicit.reduced_precision_forbidden:
        denied.update((PrecisionMode.BF16, PrecisionMode.FP16, PrecisionMode.INT8))
    if explicit.quantization_forbidden:
        denied.add(PrecisionMode.INT8)
    return explicit.model_copy(
        update={
            "denied_modes": tuple(
                mode for mode in PrecisionMode if mode in denied
            ),
        }
    )


def derive_precision_requirements(
    request: PrecisionRequirementDerivationRequest,
) -> PrecisionRequirementDerivationResult:
    """Derive stage requirements from certified state and explicit policy only."""
    if not isinstance(request, PrecisionRequirementDerivationRequest):
        raise ValueError("request must be a PrecisionRequirementDerivationRequest")
    explicit = {item.stage_id: item for item in request.explicit_requirements}
    requirements = tuple(
        _derived_requirement(request.composition, node, explicit.get(_identity(node)[0]))
        for node in request.composition.nodes
    )
    identities = tuple(_identity(node) for node in request.composition.nodes)
    requirement_set = StagePrecisionRequirementSet(
        composition=request.composition,
        requirements=requirements,
        stage_model_identities=identities,
        provenance=(
            "Phase 5 certified composition identity and exact model revisions preserved",
            "only explicit precision policy constraints were applied",
        ),
    )
    return PrecisionRequirementDerivationResult(
        requirement_set=requirement_set,
        provenance=(
            "deterministic Phase 6 requirement derivation from certified upstream state",
        ),
    )
