from mercury.reasoning_budget.difficulty import *
from mercury.reasoning_budget.cost import *
from mercury.reasoning_budget.quality_gain import *
from mercury.reasoning_budget.counterfactual import simulate_budget_alternatives
from tests.test_reasoning_budget_core import request

def test_difficulty_unknown_without_evidence():
    assert estimate_difficulty(()).difficulty is WorkloadDifficulty.UNKNOWN

def test_cost_and_quality_backends_are_uncalibrated():
    c=DeterministicReasoningCostBackend().estimate(steps=4,tokens=1024,verification_depth=1,speculation_width=2)
    q=DeterministicQualityGainBackend().estimate(difficulty="HIGH",extra_compute_units=5,evidence_ids=("e",))
    assert c.calibration_state.value=="UNCALIBRATED"
    assert q.calibration_state.value=="UNCALIBRATED"

def test_counterfactuals_are_advisory_and_deterministic():
    a=simulate_budget_alternatives(request()); b=simulate_budget_alternatives(request())
    assert a==b and all(x.advisory_only for x in a)
