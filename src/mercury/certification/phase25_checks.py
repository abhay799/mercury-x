from mercury.policy_evolution.contracts import *
from mercury.policy_evolution.engine import PolicyEvolutionEngine

def shadow_only():
    c=PolicyCandidate(policy_candidate_id="p2",parent_policy_id="p1",generation=2,artifact_version="v2",
        offline_evidence_ids=("o",),quality_floor_preserved=True,safety_preserved=True,fairness_preserved=True,
        authorization_preserved=True,rollback_policy_id="p1")
    d=PolicyEvolutionEngine().evaluate_for_shadow(c)
    return d.state is PromotionState.SHADOW and d.human_approval_required,"candidate enters shadow, not production"

def approval_required():
    c=PolicyCandidate(policy_candidate_id="p2",parent_policy_id="p1",generation=2,artifact_version="v2",
        offline_evidence_ids=("o",),shadow_evidence_ids=("s",),canary_evidence_ids=("c",),
        quality_floor_preserved=True,safety_preserved=True,fairness_preserved=True,
        authorization_preserved=True,rollback_policy_id="p1")
    try: PolicyEvolutionEngine().approve_for_production(c,approval_id=None); return False,"approval bypassed"
    except ValueError: return True,"production promotion requires explicit human approval"

CHECKS={"shadow_only":shadow_only,"approval_required":approval_required}
