import pytest
from mercury.compute_negotiator.contracts import *
from mercury.compute_negotiator.offers import generate_offers
from mercury.compute_negotiator.approval import create_approval
from mercury.compute_negotiator.commit import commit_agreement
from mercury.compute_negotiator.feasibility import *
from mercury.compute_negotiator.negotiator import decide_negotiation

def request():
    return ComputeNegotiationRequest(request_id="r",intelligence_slo_id="slo",reasoning_budget_id="b",
        placement_prediction_ids=("p",),scheduling_decision_id="sd",resource_snapshot_generation=5,requested_quality_floor=.9)

def test_offer_generator_never_lowers_quality():
    offers=generate_offers(requested_quality_floor=.9,options=(
        {"quality_floor":.85,"latency_ms":1000,"resource_units":4,"placement_candidate_ids":("p",),"speculation_width":1},
        {"quality_floor":.9,"latency_ms":1500,"resource_units":5,"placement_candidate_ids":("p",),"speculation_width":1,"changed_soft_constraints":("latency",)},
    ),protected_constraints=("quality",),resource_snapshot_generation=5)
    assert len(offers)==1 and offers[0].proposed_quality_floor==.9

def test_counteroffer_requires_explicit_approval_and_atomic_commit():
    offer=generate_offers(requested_quality_floor=.9,options=(
        {"quality_floor":.9,"latency_ms":1500,"resource_units":5,"placement_candidate_ids":("p",),"speculation_width":1,"changed_soft_constraints":("latency",)},
    ),protected_constraints=("quality",),resource_snapshot_generation=5)[0]
    decision=decide_negotiation(request=request(),feasibility_state=FeasibilityState.FEASIBLE,offers=(offer,))
    assert decision.outcome is NegotiationOutcome.COUNTEROFFER and decision.explicit_approval_required
    with pytest.raises(ValueError):
        commit_agreement(offer=offer,approval=None,current_generation=5,current_resource_snapshot_generation=5,authorization_valid=True,hard_constraints_still_hold=True)
    approval=create_approval(offer=offer,approver_authority_ref="app-owner",accepted_changed_constraints=("latency",),approval_generation=5)
    agreement=commit_agreement(offer=offer,approval=approval,current_generation=5,current_resource_snapshot_generation=5,authorization_valid=True,hard_constraints_still_hold=True)
    assert agreement.committed
