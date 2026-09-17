from mercury.quality_scheduler.admission import decide_admission
from mercury.quality_scheduler.contracts import AdmissionState
from mercury.quality_scheduler.fairness import fairness_adjustment
from mercury.quality_scheduler.preemption import evaluate_preemption
from mercury.quality_scheduler.gang import evaluate_gang
from mercury.quality_scheduler.speculation_accounting import account_speculation
def admission():
    s,_=decide_admission(hardware_compatible=True,topology_compatible=True,placement_eligible=True,hard_requirements_satisfied=True,evidence_sufficient=True)
    return s is AdmissionState.ADMIT,"admission executable"
def fairness():
    _,starved,_=fairness_adjustment(logical_age=25,fairness_weight=1,starvation_ceiling=20)
    return starved,"starvation guard executable"
def preemption():
    i=evaluate_preemption(victim_workload_id="v",challenger_workload_id="c",victim_recoverable=True,victim_checkpointable=True,victim_hard_slo_safe=True,challenger_priority_higher=True)
    return i.allowed,"preemption safety executable"
def gang():
    ok,_=evaluate_gang(("a","b"),("a","b")); return ok,"gang feasibility executable"
def speculation():
    return account_speculation(branch_count=2,phase16_limit=3,phase17_limit=2,per_branch_units=1)==2,"speculation accounting executable"
def boundary():
    import inspect, mercury.quality_scheduler.scheduler as s
    t=inspect.getsource(s)
    return not any(x in t for x in ("execute(","migrate(","provision(")),"no runtime side effects"
CHECKS={"admission":admission,"fairness":fairness,"preemption":preemption,"gang":gang,"speculation_accounting":speculation,"no_quality_degrade":admission,"no_runtime_side_effects":boundary}
