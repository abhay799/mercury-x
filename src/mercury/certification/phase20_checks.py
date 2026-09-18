from mercury.compute_negotiator.approval import create_approval
from mercury.compute_negotiator.commit import AgreementCommitLedger, commit_agreement
from mercury.compute_negotiator.concurrency import ResourceReservationGuard
from mercury.compute_negotiator.constraints import propagate_constraints
from mercury.compute_negotiator.contracts import ComputeOffer, NegotiationLifecycle
from mercury.compute_negotiator.feasibility import FeasibilityState, evaluate_feasibility
from mercury.compute_negotiator.lease import offer_is_valid
from mercury.compute_negotiator.offers import generate_offers
from mercury.compute_negotiator.revocation import should_revoke
from mercury.compute_negotiator.state import transition_lifecycle


def _raises(operation):
    try:
        operation()
    except ValueError:
        return True
    return False


def _option(quality_floor=.9, latency_ms=1000, resource_units=5, placement="p", speculation_width=1, changes=()):
    option = {
        "quality_floor": quality_floor, "latency_ms": latency_ms, "resource_units": resource_units,
        "placement_candidate_ids": (placement,), "speculation_width": speculation_width,
    }
    if changes:
        option["changed_soft_constraints"] = changes
    return option


def no_quality_reduction():
    offers = generate_offers(
        requested_quality_floor=.9,
        options=(_option(quality_floor=.85), _option(quality_floor=.9, latency_ms=1200)),
        protected_constraints=("quality",), resource_snapshot_generation=1,
    )
    preserved = offers and all(item.proposed_quality_floor >= item.requested_quality_floor for item in offers)
    contract = _raises(lambda: ComputeOffer(
        offer_id="offer", request_id="request", requested_quality_floor=.9, proposed_quality_floor=.8,
        proposed_latency_ms=1000, proposed_resource_units=5, placement_candidate_ids=("p",),
        speculation_width=1, protected_constraints=("quality", "verification", "safety", "privacy", "authorization", "residency"),
        resource_snapshot_generation=1, lease_until_generation=2, fingerprint="forged",
    ))
    return preserved and contract, "offers never propose a lower quality floor"


def feasible():
    state, _ = evaluate_feasibility(
        quality_possible=True, verification_possible=True, privacy_ok=True, residency_ok=True,
        eligible_placements=1, evidence_sufficient=True,
    )
    return state is FeasibilityState.FEASIBLE, "feasibility executable"


def constraints():
    return propagate_constraints({"quality": .9}, {"latency": 1000})["quality"] == .9, "constraint propagation executable"


def pareto_offers():
    offers = generate_offers(
        requested_quality_floor=.9,
        options=(
            _option(quality_floor=.9, latency_ms=2000, resource_units=8, placement="dominated"),
            _option(quality_floor=.95, latency_ms=1000, resource_units=4, placement="dominant"),
            _option(quality_floor=.9, latency_ms=800, resource_units=10, placement="tradeoff"),
        ),
        protected_constraints=("quality",), resource_snapshot_generation=1,
    )
    placements = {item.placement_candidate_ids[0] for item in offers}
    ok = "dominated" not in placements and {"dominant", "tradeoff"} <= placements
    return ok, "dominated offers are excluded while non-dominated tradeoffs remain"


def state():
    return transition_lifecycle(NegotiationLifecycle.REQUESTED, NegotiationLifecycle.EVALUATING) is NegotiationLifecycle.EVALUATING, "multi-round state executable"


def lease():
    offer = generate_offers(
        requested_quality_floor=.9, options=(_option(),), protected_constraints=("quality",),
        resource_snapshot_generation=1,
    )[0]
    valid, _ = offer_is_valid(offer, current_generation=1, current_resource_snapshot_generation=1)
    expired, reason = offer_is_valid(offer, current_generation=offer.lease_until_generation + 1, current_resource_snapshot_generation=1)
    return valid and (not expired) and reason == "OFFER_EXPIRED", "lease executable"


def approval():
    offer = generate_offers(
        requested_quality_floor=.9, options=(_option(changes=("latency",)),),
        protected_constraints=("quality",), resource_snapshot_generation=1,
    )[0]
    artifact = create_approval(
        offer=offer, approver_authority_ref="owner", accepted_changed_constraints=("latency",), approval_generation=1,
    )
    bound = artifact.offer_id == offer.offer_id and artifact.accepted_changed_constraints == ("latency",)
    mismatch = _raises(lambda: create_approval(
        offer=offer, approver_authority_ref="owner", accepted_changed_constraints=(), approval_generation=1,
    ))
    return bound and mismatch, "approval binds the offer and must exactly acknowledge changed constraints"


def atomic_commit():
    offer = generate_offers(
        requested_quality_floor=.9, options=(_option(changes=("latency",)),),
        protected_constraints=("quality",), resource_snapshot_generation=1,
    )[0]
    artifact = create_approval(
        offer=offer, approver_authority_ref="owner", accepted_changed_constraints=("latency",), approval_generation=1,
    )
    missing = _raises(lambda: commit_agreement(
        offer=offer, approval=None, current_generation=1, current_resource_snapshot_generation=1,
        authorization_valid=True, hard_constraints_still_hold=True,
    ))
    stale = _raises(lambda: commit_agreement(
        offer=offer, approval=artifact, current_generation=1, current_resource_snapshot_generation=2,
        authorization_valid=True, hard_constraints_still_hold=True,
    ))
    ledger = AgreementCommitLedger()
    agreement = commit_agreement(
        offer=offer, approval=artifact, current_generation=1, current_resource_snapshot_generation=1,
        authorization_valid=True, hard_constraints_still_hold=True, ledger=ledger,
    )
    replay = _raises(lambda: commit_agreement(
        offer=offer, approval=artifact, current_generation=1, current_resource_snapshot_generation=1,
        authorization_valid=True, hard_constraints_still_hold=True, ledger=ledger,
    ))
    ok = missing and stale and agreement.committed and replay
    return ok, "commit revalidates, requires approval for changes, and is exactly-once"


def concurrency():
    guard = ResourceReservationGuard()
    guard.claim("r", "a", 1)
    try:
        guard.claim("r", "b", 1)
        return False, "concurrency broken"
    except ValueError:
        return True, "concurrency guard executable"


def revoke():
    return should_revoke(resource_envelope_available=False, authorization_valid=True, hard_constraints_still_hold=True)[0], "revocation executable"


def unknown():
    state, _ = evaluate_feasibility(
        quality_possible=True, verification_possible=True, privacy_ok=True, residency_ok=True,
        eligible_placements=1, evidence_sufficient=False,
    )
    return state is FeasibilityState.UNKNOWN, "UNKNOWN fails closed"


CHECKS = {
    "no_quality_reduction": no_quality_reduction,
    "feasibility": feasible,
    "constraint_propagation": constraints,
    "pareto_offers": pareto_offers,
    "multi_round": state,
    "lease": lease,
    "approval": approval,
    "atomic_commit": atomic_commit,
    "concurrency": concurrency,
    "revocation": revoke,
    "unknown_fail_closed": unknown,
}
