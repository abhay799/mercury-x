from mercury.contracts.base import ContractModel
from pydantic import Field
from mercury.placement.contracts import PlacementPrediction
from mercury.speculation.contracts import SpeculationPlan

class PlacementConfidenceEvidence(ContractModel):
    source_prediction_id:str
    confidence_band:str
    hardware_profile_generation:int|None=Field(default=None,ge=1)
    topology_generation:int|None=Field(default=None,ge=1)
    backend_id:str
    backend_version:str
    calibration_state:str

class SpeculationCapabilityEvidence(ContractModel):
    source_plan_id:str
    max_branches:int
    plan_fingerprint:str
    candidate_fingerprints:tuple[tuple[str,str],...]

def normalize_phase15_confidence(prediction):
    if type(prediction) is not PlacementPrediction:
        raise ValueError("typed Phase 15 PlacementPrediction required")
    prediction=PlacementPrediction.model_validate(prediction.model_dump())
    return PlacementConfidenceEvidence(
        source_prediction_id=prediction.prediction_id,
        confidence_band=prediction.confidence_band.value,
        hardware_profile_generation=prediction.hardware_profile_generation,
        topology_generation=prediction.topology_generation,
        backend_id=prediction.backend_id,backend_version=prediction.backend_version,
        calibration_state=prediction.calibration_state.value)

def normalize_phase16_speculation(plan):
    if type(plan) is not SpeculationPlan:
        raise ValueError("typed Phase 16 SpeculationPlan required")
    plan=SpeculationPlan.model_validate(plan.model_dump())
    return SpeculationCapabilityEvidence(
        source_plan_id=plan.speculation_plan_id,
        max_branches=plan.max_branches,plan_fingerprint=plan.fingerprint,
        candidate_fingerprints=plan.candidate_fingerprints)
