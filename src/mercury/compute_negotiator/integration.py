from mercury.contracts.base import ContractModel
class NegotiationEvidenceBundle(ContractModel):
    intelligence_slo_id:str; reasoning_budget_id:str; scheduling_decision_id:str
    placement_prediction_ids:tuple[str,...]; speculation_plan_ids:tuple[str,...]
def build_evidence_bundle(*,slo,budget,scheduling_decision,placement_predictions,speculation_plans):
    return NegotiationEvidenceBundle(
        intelligence_slo_id=slo.intelligence_slo_id,reasoning_budget_id=budget.reasoning_budget_id,
        scheduling_decision_id=scheduling_decision.decision_id,
        placement_prediction_ids=tuple(sorted(p.prediction_id for p in placement_predictions)),
        speculation_plan_ids=tuple(sorted(p.speculation_plan_id for p in speculation_plans)))
