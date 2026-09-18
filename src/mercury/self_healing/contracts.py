from __future__ import annotations
import hashlib, json
from enum import Enum
from typing import Tuple
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

def _fp(data: dict) -> str:
    raw = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()

class HealingTrigger(str, Enum):
    NODE_FAILURE="NODE_FAILURE"; NODE_DEGRADATION="NODE_DEGRADATION"; RESOURCE_LOSS="RESOURCE_LOSS"
    SLO_RISK="SLO_RISK"; TOPOLOGY_CHANGE="TOPOLOGY_CHANGE"; EXECUTION_STALL="EXECUTION_STALL"

class HealingActionKind(str, Enum):
    RETRY="RETRY"; RESTART="RESTART"; RESCHEDULE="RESCHEDULE"; MIGRATE="MIGRATE"
    ISOLATE="ISOLATE"; DEFER="DEFER"; FAIL_SAFE="FAIL_SAFE"

class HealingLifecycle(str, Enum):
    DETECTED="DETECTED"; DIAGNOSING="DIAGNOSING"; PLANNED="PLANNED"; AUTHORIZED="AUTHORIZED"
    EXECUTING="EXECUTING"; VERIFYING="VERIFYING"; RECOVERED="RECOVERED"; FAILED="FAILED"
    ROLLED_BACK="ROLLED_BACK"; UNKNOWN="UNKNOWN"

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

class HealingRequest(FrozenArtifact):
    healing_request_id: str
    workload_id: str
    execution_id: str
    trigger: HealingTrigger
    detection_generation: int = Field(ge=0)
    topology_generation: int = Field(ge=0)
    placement_generation: int = Field(ge=0)
    scheduler_generation: int = Field(ge=0)
    slo_id: str
    slo_version: int = Field(ge=1)
    agreement_id: str
    agreement_generation: int = Field(ge=0)
    authorization_context_id: str
    authorization_generation: int = Field(ge=0)
    migration_capability_ref: str | None = None
    provenance_ids: Tuple[str, ...]

    @field_validator("healing_request_id","workload_id","execution_id","slo_id","agreement_id","authorization_context_id")
    @classmethod
    def _non_blank(cls, v):
        if not v or not v.strip(): raise ValueError("blank identity")
        return v

    @field_validator("provenance_ids")
    @classmethod
    def _prov(cls, v):
        if not v or any(not x.strip() for x in v) or len(set(v)) != len(v):
            raise ValueError("invalid provenance")
        return v

class HealingCandidate(FrozenArtifact):
    candidate_id: str
    action: HealingActionKind
    preserves_quality: bool
    preserves_safety: bool
    preserves_authorization: bool
    preserves_privacy: bool
    reversible: bool
    estimated_recovery_generations: int = Field(ge=0)
    required_resources: int = Field(ge=0)
    provenance_ids: Tuple[str, ...]

class HealingDecision(FrozenArtifact):
    decision_id: str
    healing_request_id: str
    selected_candidate_id: str
    action: HealingActionKind
    authorized: bool
    reason_codes: Tuple[str, ...]
    decision_generation: int = Field(ge=0)

class HealingVerification(FrozenArtifact):
    verification_id: str
    decision_id: str
    service_restored: bool
    slo_restored: bool
    quality_preserved: bool
    authorization_preserved: bool
    safety_preserved: bool

    @property
    def recovered(self) -> bool:
        return all((self.service_restored,self.slo_restored,self.quality_preserved,
                    self.authorization_preserved,self.safety_preserved))
