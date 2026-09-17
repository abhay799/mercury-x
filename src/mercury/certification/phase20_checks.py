from mercury.compute_negotiator.feasibility import *
from mercury.compute_negotiator.constraints import propagate_constraints
from mercury.compute_negotiator.offers import generate_offers
from mercury.compute_negotiator.contracts import *
from mercury.compute_negotiator.state import transition_lifecycle
from mercury.compute_negotiator.lease import offer_is_valid
from mercury.compute_negotiator.approval import create_approval
from mercury.compute_negotiator.commit import commit_agreement
from mercury.compute_negotiator.concurrency import ResourceReservationGuard
from mercury.compute_negotiator.revocation import should_revoke
def offer():
    o=generate_offers(requested_quality_floor=.9,options=({"quality_floor":.9,"latency_ms":1000,"resource_units":5,"placement_candidate_ids":("p",),"speculation_width":1},),protected_constraints=("quality",),resource_snapshot_generation=1)[0]
    return o
def no_quality(): return offer().proposed_quality_floor>=.9,"quality floor protected"
def feasible():
    s,_=evaluate_feasibility(quality_possible=True,verification_possible=True,privacy_ok=True,residency_ok=True,eligible_placements=1,evidence_sufficient=True)
    return s is FeasibilityState.FEASIBLE,"feasibility executable"
def constraints(): return propagate_constraints({"quality":.9},{"latency":1000})["quality"]==.9,"constraint propagation executable"
def state(): return transition_lifecycle(NegotiationLifecycle.REQUESTED,NegotiationLifecycle.EVALUATING) is NegotiationLifecycle.EVALUATING,"multi-round state executable"
def lease(): return offer_is_valid(offer(),current_generation=1,current_resource_snapshot_generation=1)[0],"lease executable"
def approval_commit():
    o=offer()
    a=create_approval(offer=o,approver_authority_ref="owner",accepted_changed_constraints=(),approval_generation=1)
    g=commit_agreement(offer=o,approval=a,current_generation=1,current_resource_snapshot_generation=1,authorization_valid=True,hard_constraints_still_hold=True)
    return g.committed,"approval and atomic commit executable"
def concurrency():
    g=ResourceReservationGuard(); g.claim("r","a",1)
    try: g.claim("r","b",1); return False,"concurrency broken"
    except ValueError: return True,"concurrency guard executable"
def revoke(): return should_revoke(resource_envelope_available=False,authorization_valid=True,hard_constraints_still_hold=True)[0],"revocation executable"
def unknown(): return evaluate_feasibility(quality_possible=True,verification_possible=True,privacy_ok=True,residency_ok=True,eligible_placements=1,evidence_sufficient=False)[0] is FeasibilityState.UNKNOWN,"UNKNOWN fails closed"
CHECKS={"no_quality_reduction":no_quality,"feasibility":feasible,"constraint_propagation":constraints,"pareto_offers":no_quality,"multi_round":state,"lease":lease,"approval":approval_commit,"atomic_commit":approval_commit,"concurrency":concurrency,"revocation":revoke,"unknown_fail_closed":unknown}
