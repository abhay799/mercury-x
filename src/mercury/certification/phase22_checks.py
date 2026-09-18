from mercury.self_healing.contracts import *
from mercury.self_healing.planner import choose_healing_candidate

def contracts():
    r=HealingRequest(healing_request_id="h",workload_id="w",execution_id="e",trigger=HealingTrigger.NODE_FAILURE,
        detection_generation=1,topology_generation=1,placement_generation=1,scheduler_generation=1,
        slo_id="s",slo_version=1,agreement_id="a",agreement_generation=1,
        authorization_context_id="auth",authorization_generation=1,provenance_ids=("p",))
    return bool(r.fingerprint),"healing request fingerprinted"

def safety():
    c=HealingCandidate(candidate_id="c",action=HealingActionKind.MIGRATE,preserves_quality=True,preserves_safety=True,
        preserves_authorization=True,preserves_privacy=True,reversible=True,estimated_recovery_generations=1,
        required_resources=1,provenance_ids=("p",))
    return choose_healing_candidate((c,)).candidate_id=="c","safe recovery candidate selected"

def reject_unsafe():
    c=HealingCandidate(candidate_id="c",action=HealingActionKind.RESTART,preserves_quality=False,preserves_safety=True,
        preserves_authorization=True,preserves_privacy=True,reversible=True,estimated_recovery_generations=1,
        required_resources=1,provenance_ids=("p",))
    try: choose_healing_candidate((c,)); return False,"unsafe candidate accepted"
    except ValueError: return True,"unsafe recovery rejected"

CHECKS={"contracts":contracts,"safety":safety,"reject_unsafe":reject_unsafe}
