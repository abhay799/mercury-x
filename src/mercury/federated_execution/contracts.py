from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Tuple

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def _fp(data: dict) -> str:
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class DomainClass(str, Enum):
    EDGE = "EDGE"
    REGION = "REGION"
    CLOUD = "CLOUD"


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


class FederationIdentity(FrozenArtifact):
    identity_id: str
    domain_id: str
    domain_class: DomainClass
    generation: int = Field(ge=0)
    authorization_context_id: str
    authorization_generation: int = Field(ge=0)
    provenance_ids: Tuple[str, ...]

    @field_validator("identity_id", "domain_id", "authorization_context_id")
    @classmethod
    def _non_blank(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("identity fields must be non-blank")
        return value


class FederationCapability(FrozenArtifact):
    capability_id: str
    domain_id: str
    domain_class: DomainClass
    generation: int = Field(ge=0)
    residency_allowed: bool
    supports_model: bool
    supports_precision: bool
    capacity_available: bool
    latency_ms: int = Field(ge=0)
    quality_preserving: bool
    authorization_context_id: str
    authorization_generation: int = Field(ge=0)
    provenance_ids: Tuple[str, ...]


class FederatedTopologySnapshot(FrozenArtifact):
    snapshot_id: str
    generation: int = Field(ge=0)
    domain_id: str
    regions: Tuple[str, ...] = ()
    edges: Tuple[str, ...] = ()
    cloud_nodes: Tuple[str, ...] = ()
    provenance_ids: Tuple[str, ...]


class FederatedPlacementDecision(FrozenArtifact):
    decision_id: str
    workload_id: str
    destination_domain_id: str
    destination_domain_class: DomainClass
    residency_ok: bool
    auth_preserved: bool
    quality_preserved: bool
    generation: int = Field(ge=0)
    evidence_ids: Tuple[str, ...] = ()


def validate_federated_placement(decision: FederatedPlacementDecision) -> bool:
    return bool(decision.residency_ok and decision.auth_preserved and decision.quality_preserved)


def validate_federation_generation(*, current_generation: int, expected_generation: int) -> tuple[bool, str]:
    if current_generation != expected_generation:
        return False, f"STALE_GENERATION:{expected_generation}>{current_generation}"
    return True, "GENERATION_CURRENT"
