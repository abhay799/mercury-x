"""Deterministic discovery of every model meeting explicit hard requirements."""

from __future__ import annotations

from pydantic import field_validator, model_validator

from mercury.contracts.base import ContractModel
from mercury.models.capabilities import ModelCapabilityRecord
from mercury.models.compatibility import (
    CompatibilityResult,
    CompatibilityStatus,
    ModelCapabilityRequirements,
    evaluate_compatibility,
)
from mercury.models.registry import ModelCapabilityRegistry


def _identity(record: ModelCapabilityRecord) -> tuple[str, str, str, str]:
    return (record.provider, record.model_id, record.family, record.revision)


class CapabilityDiscoveryQuery(ContractModel):
    """A registry and one unmodified hard requirement set to evaluate."""

    registry: ModelCapabilityRegistry
    requirements: ModelCapabilityRequirements


class CapabilityCandidate(ContractModel):
    """One compatible record and the exact compatibility evidence that admitted it."""

    record: ModelCapabilityRecord
    compatibility: CompatibilityResult

    @model_validator(mode="after")
    def candidate_is_exactly_compatible(self) -> CapabilityCandidate:
        if self.compatibility.status is not CompatibilityStatus.COMPATIBLE:
            raise ValueError("candidate compatibility must be COMPATIBLE")
        if self.compatibility.record != self.record:
            raise ValueError("candidate record must match compatibility record")
        return self


class CapabilityDiscoveryResult(ContractModel):
    """All compatible candidates in canonical identity order, never preference order."""

    requirements: ModelCapabilityRequirements
    candidates: tuple[CapabilityCandidate, ...]

    @field_validator("candidates", mode="after")
    @classmethod
    def candidates_are_canonical(
        cls, values: tuple[CapabilityCandidate, ...]
    ) -> tuple[CapabilityCandidate, ...]:
        if any(not isinstance(item, CapabilityCandidate) for item in values):
            raise ValueError("candidates must contain CapabilityCandidate values")
        normalized = tuple(sorted(values, key=lambda item: _identity(item.record)))
        identities = tuple(_identity(item.record) for item in normalized)
        if len(identities) != len(set(identities)):
            raise ValueError("candidate identities must be unique")
        return normalized


def discover_capabilities(query: CapabilityDiscoveryQuery) -> CapabilityDiscoveryResult:
    """Return every and only record compatible with the query's hard requirements."""

    if not isinstance(query, CapabilityDiscoveryQuery):
        raise ValueError("query must be a CapabilityDiscoveryQuery")
    candidates = []
    for record in query.registry.records:
        compatibility = evaluate_compatibility(record, query.requirements)
        if compatibility.status is CompatibilityStatus.COMPATIBLE:
            candidates.append(
                CapabilityCandidate(record=record, compatibility=compatibility)
            )
    return CapabilityDiscoveryResult(
        requirements=query.requirements,
        candidates=tuple(candidates),
    )
