from mercury.speculation.contracts import (
    SpeculativeBranch, SpeculativeBranchEvent, SpeculativeBranchEventType,
    SpeculativeBranchState, branch_event_payload, sh,
)
from mercury.speculation.state import _ALLOWED, transition_branch


_EVENT_BY_STATE = {
    SpeculativeBranchState.PLANNED: SpeculativeBranchEventType.PLANNED,
    SpeculativeBranchState.READY: SpeculativeBranchEventType.READY,
    SpeculativeBranchState.RUNNING: SpeculativeBranchEventType.STARTED,
    SpeculativeBranchState.SUCCEEDED: SpeculativeBranchEventType.SUCCEEDED,
    SpeculativeBranchState.FAILED: SpeculativeBranchEventType.FAILED,
    SpeculativeBranchState.COMMITTED: SpeculativeBranchEventType.COMMITTED,
    SpeculativeBranchState.CANCELLED: SpeculativeBranchEventType.CANCELLED,
    SpeculativeBranchState.DISCARDED: SpeculativeBranchEventType.DISCARDED,
}


def make_branch_event(*, branch, target_state, event_sequence, provenance_ids):
    if type(branch) is not SpeculativeBranch:
        raise ValueError("typed speculative branch required")
    if branch.speculation_plan_id is None:
        raise ValueError("branch event requires plan provenance")
    if target_state not in _ALLOWED.get(branch.state, set()):
        raise ValueError("illegal branch event transition")
    values = dict(
        speculation_plan_id=branch.speculation_plan_id, branch_id=branch.branch_id,
        candidate_id=branch.placement_candidate_id, event_type=_EVENT_BY_STATE[target_state],
        from_state=branch.state, to_state=target_state, generation=branch.generation,
        event_sequence=event_sequence, provenance_ids=tuple(sorted(provenance_ids)),
    )
    draft = SpeculativeBranchEvent.model_construct(event_id="pending", fingerprint="pending", **values)
    fingerprint = sh(branch_event_payload(draft))
    return SpeculativeBranchEvent(event_id=sh({"branch_event": fingerprint}), fingerprint=fingerprint, **values)


def apply_branch_event(branch, event):
    if type(branch) is not SpeculativeBranch or type(event) is not SpeculativeBranchEvent:
        raise ValueError("typed branch and event required")
    event = SpeculativeBranchEvent.model_validate(event.model_dump())
    if event.branch_id != branch.branch_id or event.candidate_id != branch.placement_candidate_id:
        raise ValueError("branch event targets a foreign branch")
    if event.speculation_plan_id != branch.speculation_plan_id:
        raise ValueError("branch event targets a foreign plan")
    if event.generation != branch.generation or event.from_state is not branch.state:
        raise ValueError("stale branch event")
    return transition_branch(branch, event.to_state)
