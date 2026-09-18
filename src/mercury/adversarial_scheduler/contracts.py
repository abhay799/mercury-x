from __future__ import annotations
import hashlib, json
from enum import Enum
from typing import Tuple
from pydantic import BaseModel, ConfigDict, Field, model_validator

def _fp(d): return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
class AttackKind(str, Enum):
    STARVATION="STARVATION"; PRIORITY_INVERSION="PRIORITY_INVERSION"; SPECULATION_FLOOD="SPECULATION_FLOOD"
    FRAGMENTATION="FRAGMENTATION"; STALE_STATE="STALE_STATE"; GANGLAND="GANGLAND"; TENANT_ABUSE="TENANT_ABUSE"

class FrozenArtifact(BaseModel):
    model_config=ConfigDict(frozen=True, extra="forbid")
    fingerprint:str|None=None
    def expected_fingerprint(self): return _fp(self.model_dump(mode="json", exclude={"fingerprint"}))
    @model_validator(mode="after")
    def _seal(self):
        e=self.expected_fingerprint()
        if self.fingerprint is None: object.__setattr__(self,"fingerprint",e)
        elif self.fingerprint!=e: raise ValueError("fingerprint mismatch")
        return self

class AdversarialScenario(FrozenArtifact):
    scenario_id:str
    attack_kind:AttackKind
    scheduler_generation:int=Field(ge=0)
    affected_workload_ids:Tuple[str,...]
    injected_pressure:float=Field(ge=0)
    provenance_ids:Tuple[str,...]

class SchedulerChallengeResult(FrozenArtifact):
    result_id:str
    scenario_id:str
    invariant_preserved:bool
    starvation_detected:bool
    quality_degraded:bool
    authority_leak_detected:bool
    reason_codes:Tuple[str,...]
