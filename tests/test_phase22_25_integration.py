from mercury.self_healing.contracts import *
from mercury.self_healing.engine import SelfHealingEngine
from mercury.adversarial_scheduler.contracts import *
from mercury.adversarial_scheduler.engine import AdversarialScheduler
from mercury.counterfactual_compute.contracts import *
from mercury.counterfactual_compute.simulator import CounterfactualComputeSimulator
from mercury.policy_evolution.contracts import *
from mercury.policy_evolution.engine import PolicyEvolutionEngine

def test_22_25_control_chain_is_safe_and_human_gated():
    hr=HealingRequest(healing_request_id="h",workload_id="w",execution_id="e",trigger=HealingTrigger.NODE_DEGRADATION,
        detection_generation=1,topology_generation=1,placement_generation=1,scheduler_generation=1,
        slo_id="s",slo_version=1,agreement_id="a",agreement_generation=1,
        authorization_context_id="auth",authorization_generation=1,provenance_ids=("p",))
    hc=HealingCandidate(candidate_id="c",action=HealingActionKind.MIGRATE,preserves_quality=True,preserves_safety=True,
        preserves_authorization=True,preserves_privacy=True,reversible=True,estimated_recovery_generations=1,
        required_resources=1,provenance_ids=("p",))
    assert SelfHealingEngine().plan(hr,(hc,),decision_generation=2).authorized is False

    sc=AdversarialScenario(scenario_id="a",attack_kind=AttackKind.STARVATION,scheduler_generation=1,
        affected_workload_ids=("w",),injected_pressure=1,provenance_ids=("p",))
    ar=AdversarialScheduler().evaluate(sc,invariant_preserved=True,starvation_detected=False,quality_degraded=False,authority_leak_detected=False)
    assert ar.invariant_preserved

    cfs=CounterfactualScenario(scenario_id="cf",baseline_scheduler_generation=1,hypothetical_change_id="h",change_kind="policy",provenance_ids=("p",))
    cfr=CounterfactualComputeSimulator().simulate(cfs,quality_delta=0,latency_delta_ms=-1,resource_delta=0,uncertainty=.5,evidence_ids=("e",))
    assert cfr.advisory_only

    pc=PolicyCandidate(policy_candidate_id="p2",parent_policy_id="p1",generation=2,artifact_version="v2",
        offline_evidence_ids=("o",),shadow_evidence_ids=("s",),canary_evidence_ids=("c",),
        quality_floor_preserved=True,safety_preserved=True,fairness_preserved=True,
        authorization_preserved=True,rollback_policy_id="p1")
    try:
        PolicyEvolutionEngine().approve_for_production(pc,approval_id=None)
        assert False
    except ValueError:
        pass
