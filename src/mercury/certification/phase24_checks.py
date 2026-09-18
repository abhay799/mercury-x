from mercury.counterfactual_compute.contracts import *
from mercury.counterfactual_compute.simulator import CounterfactualComputeSimulator
from mercury.counterfactual_compute.guards import enforce_advisory_only

def advisory():
    s=CounterfactualScenario(scenario_id="s",baseline_scheduler_generation=1,hypothetical_change_id="h",change_kind="placement",provenance_ids=("p",))
    r=CounterfactualComputeSimulator().simulate(s,quality_delta=0,latency_delta_ms=-10,resource_delta=1,uncertainty=.5,evidence_ids=("e",))
    return enforce_advisory_only(r) and r.advisory_only,"counterfactual remains advisory"

def unknown_fail_closed():
    s=CounterfactualScenario(scenario_id="u",baseline_scheduler_generation=1,hypothetical_change_id="h",change_kind="placement",provenance_ids=("p",))
    r=CounterfactualComputeSimulator().simulate(s,quality_delta=None,latency_delta_ms=-10,resource_delta=1)
    return r.status is CounterfactualStatus.UNKNOWN,"incomplete evidence yields UNKNOWN"

CHECKS={"advisory":advisory,"unknown_fail_closed":unknown_fail_closed}
