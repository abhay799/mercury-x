import pytest

from mercury.compute_negotiator.integration import build_evidence_bundle
from mercury.intelligence_slo.contracts import IntelligenceSLO
from mercury.placement.contracts import PlacementPrediction, PlacementConfidenceBand
from mercury.quality_scheduler.contracts import SchedulingDecision
from mercury.reasoning_budget.contracts import ReasoningBudget
from mercury.speculation.planner import build_speculation_plan


def test_phase15_through_20_bundle_preserves_typed_lineage_and_rejects_duck_types():
    placement=PlacementPrediction(prediction_id="p",candidate_id="c",raw_score=.5,
        confidence_band=PlacementConfidenceBand.MEDIUM,hardware_profile_generation=2,topology_generation=3)
    speculation=build_speculation_plan(source_segment_id="segment",candidate_ids=("c",),max_branches=1)
    budget=ReasoningBudget.model_construct(reasoning_budget_id="b",fingerprint="bf",generation=4)
    decision=SchedulingDecision.model_construct(decision_id="d",fingerprint="df",decision_generation=5)
    slo=IntelligenceSLO.model_construct(intelligence_slo_id="s",fingerprint="sf",version=6)
    bundle=build_evidence_bundle(slo=slo,budget=budget,scheduling_decision=decision,
        placement_predictions=(placement,),speculation_plans=(speculation,))
    assert bundle.placement_generations == (("p",2,3),)
    assert bundle.reasoning_budget_generation == 4 and bundle.intelligence_slo_version == 6
    with pytest.raises(ValueError,match="typed"):
        build_evidence_bundle(slo=object(),budget=budget,scheduling_decision=decision,
            placement_predictions=(placement,),speculation_plans=(speculation,))
