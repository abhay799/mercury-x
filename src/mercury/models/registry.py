"""Deterministic descriptive registry for Phase 4 model capability records."""

from __future__ import annotations

from hashlib import sha256
from json import dumps
from typing import Literal

from pydantic import model_validator

from mercury.contracts.base import ContractModel
from mercury.models.capabilities import CapabilityStatus, ModelCapabilityRecord, ModelModality
from mercury.registry.errors import RegistryEntryNotFoundError


_DeclaredCapability = Literal[
    "tool_use",
    "retrieval",
    "code_generation",
    "code_understanding",
    "structured_tool_arguments",
    "tool_result_consumption",
    "json_output",
    "schema_constrained_output",
    "streaming",
    "batching",
    "deterministic_seed",
]

_CAPABILITY_FIELDS: dict[str, str] = {
    "tool_use": "supports_tool_use",
    "retrieval": "supports_retrieval",
    "code_generation": "supports_code_generation",
    "code_understanding": "supports_code_understanding",
    "structured_tool_arguments": "supports_structured_tool_arguments",
    "tool_result_consumption": "supports_tool_result_consumption",
    "json_output": "supports_json_output",
    "schema_constrained_output": "supports_schema_constrained_output",
    "streaming": "supports_streaming",
    "batching": "supports_batching",
    "deterministic_seed": "supports_deterministic_seed",
}


def _identity(record: ModelCapabilityRecord) -> tuple[str, str, str, str]:
    return (record.provider, record.model_id, record.family, record.revision)


class ModelCapabilityRegistry(ContractModel):
    """Immutable catalog supporting exact lookup and descriptive filtering only."""

    records: tuple[ModelCapabilityRecord, ...] = ()

    @model_validator(mode="after")
    def normalize_records(self) -> ModelCapabilityRegistry:
        by_identity: dict[tuple[str, str, str, str], ModelCapabilityRecord] = {}
        for record in self.records:
            if not isinstance(record, ModelCapabilityRecord):
                raise ValueError("records must contain ModelCapabilityRecord values")
            identity = _identity(record)
            existing = by_identity.get(identity)
            if existing is not None and existing != record:
                raise ValueError("conflicting capability records share an exact identity")
            by_identity[identity] = record
        object.__setattr__(
            self, "records", tuple(by_identity[key] for key in sorted(by_identity))
        )
        return self

    @property
    def fingerprint(self) -> str:
        canonical = [record.to_dict() for record in self.records]
        payload = dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return f"sha256:{sha256(payload.encode('utf-8')).hexdigest()}"

    def list_records(self) -> tuple[ModelCapabilityRecord, ...]:
        return self.records

    def lookup(
        self, provider: str, model_id: str, family: str, revision: str
    ) -> ModelCapabilityRecord:
        identity = (provider, model_id, family, revision)
        for record in self.records:
            if _identity(record) == identity:
                return record
        raise RegistryEntryNotFoundError(
            "model capability record not found for exact identity"
        )

    def filter(
        self,
        *,
        provider: str | None = None,
        family: str | None = None,
        status: CapabilityStatus | None = None,
        input_modality: ModelModality | None = None,
        output_modality: ModelModality | None = None,
        declared_capability: _DeclaredCapability | None = None,
    ) -> tuple[ModelCapabilityRecord, ...]:
        if declared_capability is not None and declared_capability not in _CAPABILITY_FIELDS:
            raise ValueError("declared_capability must be a supported descriptive capability")
        matches = []
        for record in self.records:
            if provider is not None and record.provider != provider:
                continue
            if family is not None and record.family != family:
                continue
            if status is not None and record.status is not status:
                continue
            if input_modality is not None and input_modality not in record.input_modalities:
                continue
            if output_modality is not None and output_modality not in record.output_modalities:
                continue
            if declared_capability is not None and not getattr(
                record, _CAPABILITY_FIELDS[declared_capability]
            ):
                continue
            matches.append(record)
        return tuple(matches)
