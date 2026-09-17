from mercury.contracts.base import ContractModel
class GenericIntelligenceRequirementView(ContractModel):
    requirement_interface_id:str; quality_floor:float|None=None; confidence_floor:float|None=None
    hard_requirement_ids:tuple[str,...]=(); soft_requirement_ids:tuple[str,...]=(); unknown_requirement_ids:tuple[str,...]=()
def to_generic_requirement_view(slo):
    quality=next((r.threshold for r in slo.requirements if r.metric_id=="quality.primary"),None)
    confidence=next((r.threshold for r in slo.requirements if r.metric_id=="confidence.primary"),None)
    return GenericIntelligenceRequirementView(requirement_interface_id=slo.intelligence_slo_id,
        quality_floor=quality,confidence_floor=confidence,hard_requirement_ids=slo.hard_constraints,
        soft_requirement_ids=slo.soft_constraints,unknown_requirement_ids=slo.unknown_constraints)
