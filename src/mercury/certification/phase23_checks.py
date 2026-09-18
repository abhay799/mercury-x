from mercury.adversarial_scheduler.contracts import *
from mercury.adversarial_scheduler.engine import AdversarialScheduler
from mercury.adversarial_scheduler.invariants import challenge_passes

def robust():
    s=AdversarialScenario(scenario_id="s",attack_kind=AttackKind.STARVATION,scheduler_generation=1,
        affected_workload_ids=("w",),injected_pressure=1,provenance_ids=("p",))
    r=AdversarialScheduler().evaluate(s,invariant_preserved=True,starvation_detected=False,quality_degraded=False,authority_leak_detected=False)
    return challenge_passes(r),"robust scheduler challenge passes"

def catches_failure():
    s=AdversarialScenario(scenario_id="s2",attack_kind=AttackKind.PRIORITY_INVERSION,scheduler_generation=1,
        affected_workload_ids=("w",),injected_pressure=1,provenance_ids=("p",))
    r=AdversarialScheduler().evaluate(s,invariant_preserved=False,starvation_detected=False,quality_degraded=True,authority_leak_detected=False)
    return not challenge_passes(r),"scheduler invariant violation detected"

CHECKS={"robust":robust,"catches_failure":catches_failure}
