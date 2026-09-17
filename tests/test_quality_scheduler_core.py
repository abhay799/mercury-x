from mercury.quality_scheduler.contracts import *
from mercury.quality_scheduler.admission import decide_admission
from mercury.quality_scheduler.priority import priority_score
from mercury.quality_scheduler.fairness import fairness_adjustment
from mercury.quality_scheduler.preemption import evaluate_preemption
from mercury.quality_scheduler.gang import evaluate_gang
from mercury.quality_scheduler.speculation_accounting import account_speculation

def test_admission_and_quality_preservation():
    state,_=decide_admission(hardware_compatible=True,topology_compatible=True,placement_eligible=True,
        hard_requirements_satisfied=True,evidence_sufficient=True)
    assert state is AdmissionState.ADMIT
    state,_=decide_admission(hardware_compatible=True,topology_compatible=True,placement_eligible=True,
        hard_requirements_satisfied=False,evidence_sufficient=True)
    assert state is AdmissionState.REJECT

def test_fairness_and_preemption():
    boost,starved,_=fairness_adjustment(logical_age=25,fairness_weight=1,starvation_ceiling=20)
    assert starved and boost>0
    intent=evaluate_preemption(victim_workload_id="v",challenger_workload_id="c",
        victim_recoverable=True,victim_checkpointable=True,victim_hard_slo_safe=True,challenger_priority_higher=True)
    assert intent.allowed

def test_gang_and_speculation_bounds():
    ok,missing=evaluate_gang(("a","b"),("a","b","c"))
    assert ok and missing==()
    assert account_speculation(branch_count=2,phase16_limit=4,phase17_limit=3,per_branch_units=2)==4
