from mercury.speculation.cancellation import cancel_losing_branches
from mercury.speculation.commit import commit_verified_winner
from mercury.speculation.contracts import (
    MAX_SPECULATIVE_BRANCHES,
    SpeculationPlan,
    SpeculativeBranch,
    SpeculativeBranchState,
    SpeculativeBranchEventType,
    SpeculationRetryMetadata,
    SpeculationUpstreamProvenance,
)
from mercury.speculation.events import apply_branch_event, make_branch_event
from mercury.speculation.planner import build_speculation_plan
from mercury.speculation.state import transition_branch
from mercury.speculation.ledger import LogicalCommitLedger


def _raises_value_error(operation) -> bool:
    try:
        operation()
    except ValueError:
        return True
    return False


def _plan(candidate_ids=("candidate-1", "candidate-2")):
    return build_speculation_plan(
        source_segment_id="segment-1",
        candidate_ids=candidate_ids,
        max_branches=len(candidate_ids),
    )


def _successful(branch_id, candidate_id, result_id):
    return SpeculativeBranch(
        branch_id=branch_id,
        placement_candidate_id=candidate_id,
        state=SpeculativeBranchState.SUCCEEDED,
        result_id=result_id,
        result_fingerprint=f"fingerprint-{result_id}",
        verification_evidence_id=f"evidence-{result_id}",
        verified=True,
    )


def states():
    invalid_commit = _raises_value_error(
        lambda: SpeculativeBranch(
            branch_id="branch-1",
            placement_candidate_id="candidate-1",
            state=SpeculativeBranchState.COMMITTED,
            result_id="result-1",
            result_fingerprint="result-fingerprint-1",
            verified=False,
        )
    )
    retained_verification = _raises_value_error(
        lambda: transition_branch(
            _successful("branch-1", "candidate-1", "result-1"),
            SpeculativeBranchState.COMMITTED,
            verified=False,
        )
    )
    return (
        len(SpeculativeBranchState) == 8 and invalid_commit and retained_verification,
        "exact states and verified-result commit invariant",
    )


def bounded_fanout():
    overflow = _raises_value_error(
        lambda: build_speculation_plan(
            source_segment_id="segment-1",
            candidate_ids=tuple(f"candidate-{index}" for index in range(MAX_SPECULATIVE_BRANCHES + 1)),
            max_branches=MAX_SPECULATIVE_BRANCHES,
        )
    )
    blank_identity = _raises_value_error(
        lambda: SpeculationPlan(
            **(_plan(("candidate-1",)).model_dump() | {"source_segment_id": " "})
        )
    )
    return overflow and blank_identity, "bounded fan-out and nonblank plan identity"


def determinism():
    plan = _plan()
    winner = _successful("branch-1", "candidate-1", "result-1")
    loser = SpeculativeBranch(
        branch_id="branch-2",
        placement_candidate_id="candidate-2",
        state=SpeculativeBranchState.RUNNING,
    )
    first = commit_verified_winner(plan, (branch for branch in (loser, winner)))
    second = commit_verified_winner(plan, (winner, loser))
    cancelled_one = cancel_losing_branches((loser, winner), "branch-1")
    cancelled_two = cancel_losing_branches((winner, loser), "branch-1")
    return first == second and cancelled_one == cancelled_two, "canonical commit and cancellation ordering"


def verification_before_commit():
    plan = _plan(("candidate-1",))
    unverified = SpeculativeBranch(
        branch_id="branch-1",
        placement_candidate_id="candidate-1",
        state=SpeculativeBranchState.SUCCEEDED,
        result_id="result-1",
        result_fingerprint="result-fingerprint-1",
        verified=False,
    )
    return _raises_value_error(lambda: commit_verified_winner(plan, (unverified,))), "commit rejects unverified results"


def single_winner():
    plan = _plan()
    winner = _successful("branch-1", "candidate-1", "result-1")
    duplicate = _raises_value_error(lambda: commit_verified_winner(plan, (winner, winner)))
    unknown = _raises_value_error(
        lambda: commit_verified_winner(
            plan,
            (winner, _successful("branch-2", "unknown", "result-2")),
        )
    )
    committed = SpeculativeBranch(
        branch_id="branch-2",
        placement_candidate_id="candidate-2",
        state=SpeculativeBranchState.COMMITTED,
        result_id="result-2",
        result_fingerprint="result-fingerprint-2",
        verification_evidence_id="evidence-result-2",
        verified=True,
    )
    repeated = _raises_value_error(lambda: commit_verified_winner(plan, (winner, committed)))
    return duplicate and unknown and repeated, "unique in-plan winner and no duplicate commit"


def logical_exactly_once():
    plan = _plan()
    branches = (
        _successful("branch-1", "candidate-1", "result-1"),
        SpeculativeBranch(branch_id="branch-2", placement_candidate_id="candidate-2", state=SpeculativeBranchState.FAILED),
    )
    ledger = LogicalCommitLedger()
    first = ledger.commit(plan, branches)
    replay = ledger.commit(plan, branches)
    competing = (
        branches[0].model_copy(update={"verified": False, "verification_evidence_id": None}),
        _successful("branch-2", "candidate-2", "result-2"),
    )
    rejected = _raises_value_error(lambda: ledger.commit(plan, competing))
    return first == replay and rejected, "logical commit replay is idempotent and competing winner is rejected"


def accounting_metadata():
    plan = _plan()
    result = commit_verified_winner(
        plan,
        (_successful("branch-1", "candidate-1", "result-1"), _successful("branch-2", "candidate-2", "result-2")),
    )
    return result.branch_count == 2 and result.verified_success_count == 2, "branch and verification accounting is explicit"


def no_migration():
    import inspect
    import mercury.speculation.commit as commit

    return "migrate(" not in inspect.getsource(commit), "no migration behavior"


def branch_events():
    plan = _plan(("candidate-1",))
    branch = SpeculativeBranch(
        branch_id="branch-1", placement_candidate_id="candidate-1",
        state=SpeculativeBranchState.PLANNED, speculation_plan_id=plan.speculation_plan_id,
        source_segment_id=plan.source_segment_id, plan_fingerprint=plan.fingerprint,
        candidate_fingerprint=dict(plan.candidate_fingerprints)["candidate-1"], generation=1,
    )
    event = make_branch_event(branch=branch, target_state=SpeculativeBranchState.READY,
                              event_sequence=1, provenance_ids=("cert",))
    transitioned = apply_branch_event(branch, event)
    stale = _raises_value_error(lambda: apply_branch_event(transitioned, event))
    return event.event_type is SpeculativeBranchEventType.READY and transitioned.state is SpeculativeBranchState.READY and stale, "branch events are typed, content-addressed, and reject stale replay"


def retry_policy():
    baseline = SpeculationRetryMetadata()
    attempted = _raises_value_error(lambda: SpeculationRetryMetadata(retry_supported=True, retry_attempt=1, maximum_attempts=1))
    return not baseline.retry_supported and attempted, "Phase 16 retry is explicitly unsupported and hidden retries reject"


def upstream_lineage():
    provenance = SpeculationUpstreamProvenance(
        candidate_id="candidate-1", candidate_fingerprint="candidate-fingerprint",
        hardware_profile_id="profile", hardware_profile_generation=1,
        hardware_profile_fingerprint="profile-fingerprint", topology_graph_id="graph",
        topology_generation=1, path_result_id="path", path_result_fingerprint="path-fingerprint",
        prediction_id="prediction", prediction_fingerprint="prediction-fingerprint",
    )
    plan = _plan(("candidate-1",))
    payload = plan.model_dump() | {"upstream_provenance": (provenance,)}
    return _raises_value_error(lambda: SpeculationPlan.model_validate(payload)), "foreign upstream lineage cannot be attached without changing the content-addressed plan"


CHECKS = {
    "states": states,
    "bounded_fanout": bounded_fanout,
    "determinism": determinism,
    "verification_before_commit": verification_before_commit,
    "single_winner": single_winner,
    "logical_exactly_once": logical_exactly_once,
    "accounting_metadata": accounting_metadata,
    "branch_events": branch_events,
    "retry_policy": retry_policy,
    "upstream_lineage": upstream_lineage,
    "no_migration": no_migration,
}
