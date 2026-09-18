import hashlib
import json
from enum import Enum

from pydantic import Field, field_validator, model_validator

from mercury.contracts.base import ContractModel


class RequirementEnvelopeStatus(str, Enum):
    ACTIVE = "ACTIVE"
    AMBIGUOUS = "AMBIGUOUS"
    UNSATISFIABLE = "UNSATISFIABLE"
    INVALID = "INVALID"


def _hash(payload) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()


def make_requirement_envelope_fingerprint(**values) -> str:
    payload = dict(values)
    status = payload.get("status")
    if isinstance(status, RequirementEnvelopeStatus):
        payload["status"] = status.value
    for name in ("hard_requirement_ids", "soft_requirement_ids", "unknown_requirement_ids", "provenance_ids"):
        payload[name] = list(sorted(payload.get(name, ())))
    return _hash(payload)


class GenericIntelligenceRequirementEnvelope(ContractModel):
    requirement_interface_id: str
    source_slo_id: str
    source_slo_version: int = Field(ge=1)
    source_slo_fingerprint: str
    status: RequirementEnvelopeStatus
    quality_floor: float | None = Field(default=None, ge=0, le=1)
    confidence_floor: float | None = Field(default=None, ge=0, le=1)
    hard_requirement_ids: tuple[str, ...]
    soft_requirement_ids: tuple[str, ...] = ()
    unknown_requirement_ids: tuple[str, ...] = ()
    degradation_allowed: bool = False
    provenance_ids: tuple[str, ...]
    fingerprint: str

    @field_validator("requirement_interface_id", "source_slo_id", "source_slo_fingerprint", "fingerprint")
    @classmethod
    def nonblank_identity(cls, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("requirement envelope identity must be nonblank")
        return value

    @field_validator("hard_requirement_ids", "soft_requirement_ids", "unknown_requirement_ids", "provenance_ids")
    @classmethod
    def canonical_ids(cls, values, info):
        values = tuple(values)
        if any(not isinstance(value, str) or not value.strip() for value in values):
            raise ValueError(f"{info.field_name} must be nonblank")
        if len(values) != len(set(values)):
            raise ValueError(f"{info.field_name} contains duplicates")
        return tuple(sorted(values))

    @model_validator(mode="after")
    def protect_and_validate(self):
        if self.degradation_allowed:
            raise ValueError("generic requirement envelope cannot enable degradation")
        if not self.provenance_ids:
            raise ValueError("requirement envelope requires provenance")
        expected = make_requirement_envelope_fingerprint(
            **self.model_dump(exclude={"fingerprint"})
        )
        if self.fingerprint != expected:
            raise ValueError("requirement envelope fingerprint mismatch")
        return self


def validate_active_requirement_envelope(envelope):
    if type(envelope) is not GenericIntelligenceRequirementEnvelope:
        raise ValueError("typed generic intelligence requirement envelope required")
    envelope = GenericIntelligenceRequirementEnvelope.model_validate(envelope.model_dump())
    if envelope.status is not RequirementEnvelopeStatus.ACTIVE or envelope.unknown_requirement_ids:
        raise ValueError("UNKNOWN or inactive intelligence requirements fail closed")
    return envelope
