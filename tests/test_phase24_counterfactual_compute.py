from mercury.counterfactual_compute.contracts import *
from mercury.counterfactual_compute.simulator import CounterfactualComputeSimulator
from mercury.counterfactual_compute.guards import enforce_advisory_only

def test_counterfactual_is_advisory_and_uncalibrated():
    s=CounterfactualScenario(scenario_id="s",baseline_scheduler_generation=1,hypothetical_change_id="h",change_kind="placement",provenance_ids=("p",))
    r=CounterfactualComputeSimulator().simulate(s,quality_delta=0,latency_delta_ms=-5,resource_delta=1,uncertainty=.4,evidence_ids=("e",))
    assert r.status is CounterfactualStatus.VALID
    assert enforce_advisory_only(r)

def test_missing_dimension_yields_unknown():
    s=CounterfactualScenario(scenario_id="u",baseline_scheduler_generation=1,hypothetical_change_id="h",change_kind="placement",provenance_ids=("p",))
    r=CounterfactualComputeSimulator().simulate(s,quality_delta=None,latency_delta_ms=1,resource_delta=1)
    assert r.status is CounterfactualStatus.UNKNOWN
