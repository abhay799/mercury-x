from __future__ import annotations
import hashlib, json
from enum import Enum
from typing import Tuple
from pydantic import BaseModel, ConfigDict, Field, model_validator

def _fp(d): return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
class CounterfactualStatus(str, Enum): VALID="VALID"; INVALID="INVALID"; UNKNOWN="UNKNOWN"
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

class CounterfactualScenario(FrozenArtifact):
    scenario_id:str
    baseline_scheduler_generation:int=Field(ge=0)
    hypothetical_change_id:str
    change_kind:str
    provenance_ids:Tuple[str,...]

class CounterfactualResult(FrozenArtifact):
    result_id:str
    scenario_id:str
    status:CounterfactualStatus
    predicted_quality_delta:float|None=None
    predicted_latency_delta_ms:float|None=None
    predicted_resource_delta:float|None=None
    uncertainty:float=Field(ge=0,le=1)
    calibration_state:str="UNCALIBRATED"
    advisory_only:bool=True
    evidence_ids:Tuple[str,...]=()
