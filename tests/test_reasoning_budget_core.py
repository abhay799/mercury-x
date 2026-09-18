import pytest
from mercury.reasoning_budget.contracts import *
from mercury.reasoning_budget.frontier import build_budget_frontier
from mercury.reasoning_budget.lifecycle import build_reasoning_budget
from mercury.reasoning_budget.control import evaluate_escalation

def request():
    return ReasoningBudgetRequest(request_id="r",workload_id="w",segment_id="s",requirement_interface_id="req",quality_metric_id="quality.primary",
        quality_floor=.9,confidence_floor=.8,max_reasoning_steps=8,max_tokens=4096,max_compute_units=50,
        max_speculative_branches=4,verification_depth_min=1,latency_ceiling_ms=2000,
        escalation_policy_id="escalate",stop_policy_id="stop",provenance_ids=("p",))

def candidate(cid,q=.92,c=10,lat=1000,u=.2):
    return ReasoningBudgetCandidate(candidate_id=cid,reasoning_steps=4,max_tokens=2048,compute_units=c,
        verification_depth=1,speculation_width=2,expected_quality_low=q,expected_quality_high=min(1,q+.03),
        expected_latency_ms=lat,uncertainty=u,evidence_ids=("e",))

def test_frontier_and_budget_preserve_quality():
    r=request(); a=candidate("a"); b=candidate("b",q=.90,c=20,lat=1500,u=.4)
    f=build_budget_frontier((b,a))
    assert tuple(x.candidate_id for x in f)==("a",)
    budget=build_reasoning_budget(r,a)
    assert budget.quality_floor==.9
    assert budget.calibration_state is BudgetCalibrationState.UNCALIBRATED

def test_quality_below_floor_rejected():
    with pytest.raises(ValueError):
        build_reasoning_budget(request(),candidate("x",q=.8))

def test_escalation_on_quality_shortfall():
    yes,reasons=evaluate_escalation(quality_met=False,confidence_met=True,verification_passed=True,uncertainty_ok=True,branches_agree=True,hard_ceiling_reached=False)
    assert yes and "QUALITY_SHORTFALL" in reasons
