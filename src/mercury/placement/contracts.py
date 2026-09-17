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

def stable_hash(payload):
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()
