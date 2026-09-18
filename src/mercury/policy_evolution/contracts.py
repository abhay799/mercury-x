from __future__ import annotations
import hashlib, json
from enum import Enum
from typing import Tuple
from pydantic import BaseModel, ConfigDict, Field, model_validator

def _fp(d): return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
class PromotionState(str, Enum): PROPOSED="PROPOSED"; SHADOW="SHADOW"; CANARY="CANARY"; APPROVED="APPROVED"; REJECTED="REJECTED"; ROLLED_BACK="ROLLED_BACK"

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

class PolicyCandidate(FrozenArtifact):
    policy_candidate_id:str
    parent_policy_id:str
    generation:int=Field(ge=1)
    artifact_version:str
    offline_evidence_ids:Tuple[str,...]
    shadow_evidence_ids:Tuple[str,...]=()
    canary_evidence_ids:Tuple[str,...]=()
    quality_floor_preserved:bool
    safety_preserved:bool
    fairness_preserved:bool
    authorization_preserved:bool
    rollback_policy_id:str

class PromotionDecision(FrozenArtifact):
    decision_id:str
    policy_candidate_id:str
    state:PromotionState
    human_approval_required:bool=True
    human_approval_id:str|None=None
    reason_codes:Tuple[str,...]
