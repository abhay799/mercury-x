from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Tuple

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def _fp(data: dict) -> str:
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class DataClassification(str, Enum):
    UNKNOWN = "UNKNOWN"
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    SENSITIVE = "SENSITIVE"
    RESTRICTED = "RESTRICTED"


class FrozenArtifact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    fingerprint: str | None = None

    def expected_fingerprint(self) -> str:
        return _fp(self.model_dump(mode="json", exclude={"fingerprint"}))

    @model_validator(mode="after")
    def _seal(self):
        expected = self.expected_fingerprint()
        if self.fingerprint is None:
            object.__setattr__(self, "fingerprint", expected)
        elif self.fingerprint != expected:
            raise ValueError("fingerprint mismatch")
        return self


class PrivacyPolicy(FrozenArtifact):
    policy_id: str
    classification: DataClassification
    purpose: str
    scope: str
    residency_ok: bool
    retention_days: int = Field(ge=0)
    provenance_ids: Tuple[str, ...]


class PrivacyEnvelope(FrozenArtifact):
    envelope_id: str
    workload_id: str
    classification: DataClassification
    purpose: str
    scope: str
    enforced: bool = True
    minimum_necessary: bool = True
    redact_logs: bool = True
    allow_cache: bool = True
    allow_logging: bool = False
    provenance_ids: Tuple[str, ...] = ()


def evaluate_privacy_policy(policy: PrivacyPolicy, *, classification: DataClassification | None) -> bool:
    if classification is None or classification == DataClassification.UNKNOWN:
        return False
    if not policy.residency_ok:
        return False
    return policy.classification == classification
