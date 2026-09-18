from mercury.contracts.base import ContractModel
from mercury.placement.contracts import PlacementPrediction
from mercury.speculation.contracts import SpeculationPlan
from mercury.reasoning_budget.contracts import ReasoningBudget
from mercury.quality_scheduler.contracts import SchedulingDecision
from mercury.intelligence_slo.contracts import IntelligenceSLO
class NegotiationEvidenceBundle(ContractModel):
    intelligence_slo_id:str; reasoning_budget_id:str; scheduling_decision_id:str
    placement_prediction_ids:tuple[str,...]; speculation_plan_ids:tuple[str,...]
    intelligence_slo_fingerprint:str; intelligence_slo_version:int
    reasoning_budget_fingerprint:str; reasoning_budget_generation:int
    scheduling_decision_fingerprint:str; scheduling_decision_generation:int
    placement_generations:tuple[tuple[str,int|None,int|None],...]
    speculation_plan_fingerprints:tuple[tuple[str,str],...]
def build_evidence_bundle(*,slo,budget,scheduling_decision,placement_predictions,speculation_plans):
    if type(slo) is not IntelligenceSLO or type(budget) is not ReasoningBudget or type(scheduling_decision) is not SchedulingDecision:
        raise ValueError("typed Phase 17-19 evidence required")
    if any(type(item) is not PlacementPrediction for item in placement_predictions): raise ValueError("typed Phase 15 evidence required")
    if any(type(item) is not SpeculationPlan for item in speculation_plans): raise ValueError("typed Phase 16 evidence required")
    return NegotiationEvidenceBundle(
        intelligence_slo_id=slo.intelligence_slo_id,reasoning_budget_id=budget.reasoning_budget_id,
        scheduling_decision_id=scheduling_decision.decision_id,
        placement_prediction_ids=tuple(sorted(p.prediction_id for p in placement_predictions)),
        speculation_plan_ids=tuple(sorted(p.speculation_plan_id for p in speculation_plans)),
        intelligence_slo_fingerprint=slo.fingerprint,intelligence_slo_version=slo.version,
        reasoning_budget_fingerprint=budget.fingerprint,reasoning_budget_generation=budget.generation,
        scheduling_decision_fingerprint=scheduling_decision.fingerprint,scheduling_decision_generation=scheduling_decision.decision_generation,
        placement_generations=tuple(sorted((p.prediction_id,p.hardware_profile_generation,p.topology_generation) for p in placement_predictions)),
        speculation_plan_fingerprints=tuple(sorted((p.speculation_plan_id,p.fingerprint) for p in speculation_plans)))
