from mercury.adversarial_scheduler.contracts import *
from mercury.adversarial_scheduler.engine import AdversarialScheduler
from mercury.adversarial_scheduler.invariants import challenge_passes

def test_adversarial_scheduler_detects_quality_failure():
    s=AdversarialScenario(scenario_id="s",attack_kind=AttackKind.SPECULATION_FLOOD,scheduler_generation=1,
        affected_workload_ids=("w",),injected_pressure=10,provenance_ids=("p",))
    r=AdversarialScheduler().evaluate(s,invariant_preserved=False,starvation_detected=False,quality_degraded=True,authority_leak_detected=False)
    assert not challenge_passes(r)
    assert "QUALITY_DEGRADATION" in r.reason_codes

def test_robust_case_passes():
    s=AdversarialScenario(scenario_id="r",attack_kind=AttackKind.STALE_STATE,scheduler_generation=1,
        affected_workload_ids=("w",),injected_pressure=1,provenance_ids=("p",))
    r=AdversarialScheduler().evaluate(s,invariant_preserved=True,starvation_detected=False,quality_degraded=False,authority_leak_detected=False)
    assert challenge_passes(r)
