import pytest
from mercury.self_healing.contracts import *
from mercury.self_healing.engine import SelfHealingEngine
from mercury.self_healing.state import transition
from mercury.self_healing.ledger import HealingLedger

def req():
    return HealingRequest(healing_request_id="h",workload_id="w",execution_id="e",trigger=HealingTrigger.NODE_FAILURE,
        detection_generation=1,topology_generation=1,placement_generation=1,scheduler_generation=1,
        slo_id="s",slo_version=1,agreement_id="a",agreement_generation=1,
        authorization_context_id="auth",authorization_generation=1,provenance_ids=("p",))

def cand(**kw):
    v=dict(candidate_id="c",action=HealingActionKind.MIGRATE,preserves_quality=True,preserves_safety=True,
        preserves_authorization=True,preserves_privacy=True,reversible=True,estimated_recovery_generations=1,
        required_resources=1,provenance_ids=("p",))
    v.update(kw); return HealingCandidate(**v)

def test_safe_planning_and_immutability():
    d=SelfHealingEngine().plan(req(),(cand(),),decision_generation=2)
    assert d.action is HealingActionKind.MIGRATE and not d.authorized

def test_unsafe_candidate_rejected():
    with pytest.raises(ValueError): SelfHealingEngine().plan(req(),(cand(preserves_quality=False),),decision_generation=2)

def test_lifecycle_and_ledger():
    assert transition(HealingLifecycle.DETECTED,HealingLifecycle.DIAGNOSING) is HealingLifecycle.DIAGNOSING
    with pytest.raises(ValueError): transition(HealingLifecycle.DETECTED,HealingLifecycle.RECOVERED)
    l=HealingLedger(); l.append("e1",{"x":1})
    with pytest.raises(ValueError): l.append("e1",{"x":2})
