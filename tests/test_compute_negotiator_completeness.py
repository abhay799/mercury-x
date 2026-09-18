from concurrent.futures import ThreadPoolExecutor

import pytest
from pydantic import ValidationError

from mercury.compute_negotiator.approval import create_approval
from mercury.compute_negotiator.commit import AgreementCommitLedger, commit_agreement
from mercury.compute_negotiator.contracts import (
    NegotiationEventType,
    NegotiationLifecycle,
    NegotiationRound,
)
from mercury.compute_negotiator.history import append_history_event, empty_history
from mercury.compute_negotiator.offers import generate_offers
from mercury.reasoning_budget.contracts import canonical_hash


def offer(*, changes=()):
    return generate_offers(
        request_id="request-1",
        requested_quality_floor=.9,
        options=({
            "quality_floor": .9,
            "latency_ms": 1000,
            "resource_units": 5,
            "placement_candidate_ids": ("placement-1",),
            "speculation_width": 1,
            "changed_soft_constraints": changes,
        },),
        protected_constraints=("quality", "verification", "safety", "privacy", "authorization", "residency"),
        resource_snapshot_generation=3,
    )[0]


@pytest.mark.parametrize("name", ("quality", "verification", "safety", "privacy", "authorization", "residency"))
def test_protected_constraints_can_never_be_changed(name):
    with pytest.raises(ValueError, match="protected"):
        offer(changes=(name,))


def test_offer_and_approval_integrity_is_content_addressed():
    item = offer(changes=("latency",))
    with pytest.raises(ValidationError, match="fingerprint"):
        type(item).model_validate({**item.model_dump(), "proposed_latency_ms": 999, "fingerprint": "forged"})
    approval = create_approval(
        offer=item,
        approver_authority_ref="authority-1",
        accepted_changed_constraints=("latency",),
        approval_generation=3,
    )
    with pytest.raises(ValidationError, match="fingerprint"):
        type(approval).model_validate({**approval.model_dump(), "approver_authority_ref": "attacker"})


def test_approval_generation_and_exact_changes_are_revalidated_at_commit():
    item = offer(changes=("latency",))
    approval = create_approval(
        offer=item,
        approver_authority_ref="authority-1",
        accepted_changed_constraints=("latency",),
        approval_generation=2,
    )
    with pytest.raises(ValueError, match="generation"):
        commit_agreement(
            offer=item, approval=approval, current_generation=3,
            current_resource_snapshot_generation=3, authorization_valid=True,
            hard_constraints_still_hold=True,
        )


def test_negotiation_round_is_immutable_and_lineage_bound():
    item = offer()
    body = {
        "request_id": "request-1", "round_generation": 1,
        "previous_round_id": None, "lifecycle": "OFFERED",
        "offer_ids": [item.offer_id], "resource_snapshot_generation": 3,
        "provenance_ids": [item.offer_id],
    }
    fingerprint = canonical_hash(body)
    round_ = NegotiationRound(
        round_id=canonical_hash({"negotiation_round": fingerprint}),
        request_id="request-1", round_generation=1, previous_round_id=None,
        lifecycle=NegotiationLifecycle.OFFERED, offer_ids=(item.offer_id,),
        resource_snapshot_generation=3, provenance_ids=(item.offer_id,),
        fingerprint=fingerprint,
    )
    with pytest.raises(ValidationError):
        round_.round_generation = 2


def test_history_is_typed_append_only_and_tamper_evident():
    history = empty_history("request-1")
    updated = append_history_event(
        history, event_type=NegotiationEventType.OFFERED,
        artifact_id=offer().offer_id, generation=1,
        provenance_ids=("request-1",),
    )
    assert history.events == () and updated.events[0].sequence == 1
    with pytest.raises(ValidationError, match="fingerprint"):
        type(updated.events[0]).model_validate({**updated.events[0].model_dump(), "artifact_id": "forged"})


def test_exactly_once_commit_is_atomic_under_concurrency():
    item = offer()
    ledger = AgreementCommitLedger()

    def attempt():
        try:
            return commit_agreement(
                offer=item, approval=None, current_generation=3,
                current_resource_snapshot_generation=3, authorization_valid=True,
                hard_constraints_still_hold=True, ledger=ledger,
            ).agreement_id
        except ValueError:
            return None

    with ThreadPoolExecutor(max_workers=8) as pool:
        outcomes = tuple(pool.map(lambda _: attempt(), range(16)))
    assert len([value for value in outcomes if value is not None]) == 1
