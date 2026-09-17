import hashlib, json
from enum import Enum
from pydantic import Field, field_validator
from mercury.contracts.base import ContractModel

class PlacementConfidenceBand(str,Enum):
    LOW="LOW"; MEDIUM="MEDIUM"; HIGH="HIGH"
class PlacementCalibrationState(str,Enum):
    UNCALIBRATED="UNCALIBRATED"; EMPIRICALLY_CALIBRATED="EMPIRICALLY_CALIBRATED"

class PlacementCandidate(ContractModel):
    candidate_id:str; segment_id:str; topology_node_id:str; hardware_profile_id:str
    eligible:bool; reason_codes:tuple[str,...]=()
    topology_graph_id: str | None = None
    topology_generation: int | None = Field(default=None, ge=1)
    evidence_ids: tuple[str, ...] = ()

    @field_validator("candidate_id", "segment_id", "topology_node_id", "hardware_profile_id", "topology_graph_id")
    @classmethod
    def nonblank_ids(cls, value):
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise ValueError("placement identity must be nonblank")
        return value

    @field_validator("reason_codes", "evidence_ids")
    @classmethod
    def canonical_strings(cls, values):
        values = tuple(values)
        if any(not isinstance(value, str) or not value.strip() for value in values):
            raise ValueError("placement strings must be nonblank")
        if len(values) != len(set(values)):
            raise ValueError("placement strings must be unique")
        return tuple(sorted(values))
class PlacementFeatures(ContractModel):
    candidate_id:str
    compatibility_score:float=Field(ge=0,le=1)
    locality_score:float=Field(ge=0,le=1)
    evidence_score:float=Field(ge=0,le=1)
    uncertainty_penalty:float=Field(ge=0,le=1)
class PlacementPrediction(ContractModel):
    prediction_id:str; candidate_id:str; raw_score:float
    confidence_band:PlacementConfidenceBand
    calibration_state:PlacementCalibrationState=PlacementCalibrationState.UNCALIBRATED
    reason_codes:tuple[str,...]=()
    backend_id: str = "deterministic-weighted"
    backend_version: str = "v1"

    @field_validator("backend_id", "backend_version")
    @classmethod
    def backend_identity(cls, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("placement backend identity must be nonblank")
        return value

def stable_hash(payload):
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()
