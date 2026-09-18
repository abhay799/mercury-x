import pytest
from mercury.policy_evolution.contracts import *
from mercury.policy_evolution.engine import PolicyEvolutionEngine

def candidate(**kw):
    v=dict(policy_candidate_id="p2",parent_policy_id="p1",generation=2,artifact_version="v2",
        offline_evidence_ids=("o",),shadow_evidence_ids=("s",),canary_evidence_ids=("c",),
        quality_floor_preserved=True,safety_preserved=True,fairness_preserved=True,
        authorization_preserved=True,rollback_policy_id="p1")
    v.update(kw); return PolicyCandidate(**v)

def test_shadow_before_production():
    d=PolicyEvolutionEngine().evaluate_for_shadow(candidate(shadow_evidence_ids=(),canary_evidence_ids=()))
    assert d.state is PromotionState.SHADOW and d.human_approval_required

def test_production_requires_evidence_and_human_approval():
    with pytest.raises(ValueError): PolicyEvolutionEngine().approve_for_production(candidate(),approval_id=None)
    with pytest.raises(ValueError): PolicyEvolutionEngine().approve_for_production(candidate(canary_evidence_ids=()),approval_id="human-1")
    d=PolicyEvolutionEngine().approve_for_production(candidate(),approval_id="human-1")
    assert d.state is PromotionState.APPROVED and d.human_approval_id=="human-1"
