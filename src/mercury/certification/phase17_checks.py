from mercury.reasoning_budget.contracts import *
from mercury.reasoning_budget.frontier import build_budget_frontier
from mercury.reasoning_budget.lifecycle import build_reasoning_budget
from mercury.reasoning_budget.control import evaluate_escalation
def behavior():
    r=ReasoningBudgetRequest(request_id="r",segment_id="s",quality_metric_id="q",quality_floor=.9,confidence_floor=.8,max_reasoning_steps=8,max_tokens=4096,max_compute_units=20,max_speculative_branches=3,verification_depth_min=1,latency_ceiling_ms=2000)
    c=ReasoningBudgetCandidate(candidate_id="c",reasoning_steps=4,max_tokens=2048,compute_units=10,verification_depth=1,speculation_width=2,expected_quality_low=.92,expected_quality_high=.95,expected_latency_ms=1000,uncertainty=.2,evidence_ids=("e",))
    b=build_reasoning_budget(r,c)
    return b.quality_floor==.9 and b.calibration_state is BudgetCalibrationState.UNCALIBRATED,"budget preserves quality and calibration honesty"
def frontier():
    return build_budget_frontier(())==(),"frontier executable"
def escalation():
    yes,_=evaluate_escalation(quality_met=False,confidence_met=True,verification_passed=True,uncertainty_ok=True,branches_agree=True,hard_ceiling_reached=False)
    return yes,"escalation executable"
def boundary():
    import inspect, mercury.reasoning_budget.lifecycle as m
    t=inspect.getsource(m)
    return not any(x in t for x in ("schedule(","migrate(","provision(","select_model")), "no forbidden authority"
CHECKS={"contracts":behavior,"quality_floor":behavior,"frontier":frontier,"escalation":escalation,"uncalibrated":behavior,"no_cross_phase_authority":boundary}
