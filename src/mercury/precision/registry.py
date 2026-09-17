"""Exact, deterministic registry for Phase 6 precision capabilities."""

from __future__ import annotations

from hashlib import sha256
from json import dumps
from typing import Literal

from pydantic import field_validator, model_validator

from mercury.contracts.base import ContractModel
from mercury.precision.contracts import ModelPrecisionCapability


def _nonblank(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be nonblank")
    return value


def canonical_precision_model_identity(
    record: ModelPrecisionCapability,
) -> tuple[str, str, str, str]:
    """Return the exact provider/model/family/revision identity without inference."""
    if not isinstance(record, ModelPrecisionCapability):
        raise ValueError("record must be a ModelPrecisionCapability")
    return record.provider, record.model_id, record.family, record.revision


class PrecisionRegistryIssue(ContractModel):
    issue_id: str
    identity: tuple[str, str, str, str] | None = None
    reason: str

    @field_validator("issue_id", "reason")
    @classmethod
    def values_are_nonblank(cls, value: str) -> str:
        return _nonblank(value, "precision registry issue value")

    @field_validator("identity")
    @classmethod
    def identity_is_nonblank(
        cls, value: tuple[str, str, str, str] | None
    ) -> tuple[str, str, str, str] | None:
        if value is None:
            return None
        if any(not isinstance(item, str) or not item.strip() for item in value):
            raise ValueError("registry issue identity must contain nonblank values")
        return value


class ModelPrecisionCapabilityRegistry(ContractModel):
    schema_version: Literal["mercury.model-precision-registry/v1"] = (
        "mercury.model-precision-registry/v1"
    )
    records: tuple[ModelPrecisionCapability, ...]

    @field_validator("records", mode="after")
    @classmethod
    def records_are_exact_and_canonical(
        cls, values: tuple[ModelPrecisionCapability, ...]
    ) -> tuple[ModelPrecisionCapability, ...]:
        if any(not isinstance(value, ModelPrecisionCapability) for value in values):
            raise ValueError("records must contain ModelPrecisionCapability values")
        records_by_identity: dict[tuple[str, str, str, str], ModelPrecisionCapability] = {}
        for record in values:
            identity = canonical_precision_model_identity(record)
            existing = records_by_identity.get(identity)
            if existing is not None and existing != record:
                raise ValueError("conflicting precision declarations share one exact identity")
            records_by_identity[identity] = record
        return tuple(
            records_by_identity[identity] for identity in sorted(records_by_identity)
        )

    @property
    def fingerprint(self) -> str:
        """Return a stable digest of canonical exact capability declarations."""
        payload = [record.model_dump(mode="json") for record in self.records]
        canonical = dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return f"sha256:{sha256(canonical.encode('utf-8')).hexdigest()}"


def lookup_exact_precision_capability(
    registry: ModelPrecisionCapabilityRegistry,
    provider: str,
    model_id: str,
    family: str,
    revision: str,
) -> ModelPrecisionCapability | None:
    """Return one capability only when every exact identity component matches."""
    if not isinstance(registry, ModelPrecisionCapabilityRegistry):
        raise ValueError("registry must be a ModelPrecisionCapabilityRegistry")
    identity = (
        _nonblank(provider, "provider"),
        _nonblank(model_id, "model_id"),
        _nonblank(family, "family"),
        _nonblank(revision, "revision"),
    )
    for record in registry.records:
        if canonical_precision_model_identity(record) == identity:
            return record
    return None
