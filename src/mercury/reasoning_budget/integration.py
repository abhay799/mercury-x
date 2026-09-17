from mercury.contracts.base import ContractModel

class PlacementConfidenceEvidence(ContractModel):
    source_prediction_id:str
    confidence_band:str

class SpeculationCapabilityEvidence(ContractModel):
    source_plan_id:str
    max_branches:int

def normalize_phase15_confidence(prediction):
    return PlacementConfidenceEvidence(
        source_prediction_id=prediction.prediction_id,
        confidence_band=prediction.confidence_band.value)

def normalize_phase16_speculation(plan):
    return SpeculationCapabilityEvidence(
        source_plan_id=plan.speculation_plan_id,
        max_branches=plan.max_branches)
