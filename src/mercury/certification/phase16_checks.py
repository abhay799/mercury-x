from mercury.speculation.cancellation import cancel_losing_branches
from mercury.speculation.commit import commit_verified_winner
from mercury.speculation.contracts import (
    MAX_SPECULATIVE_BRANCHES,
    SpeculationPlan,
    SpeculativeBranch,
    SpeculativeBranchState,
)
from mercury.speculation.planner import build_speculation_plan
from mercury.speculation.state import transition_branch


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


def no_migration():
    import inspect
    import mercury.speculation.commit as commit

    return "migrate(" not in inspect.getsource(commit), "no migration behavior"


CHECKS = {
    "states": states,
    "bounded_fanout": bounded_fanout,
    "determinism": determinism,
    "verification_before_commit": verification_before_commit,
    "single_winner": single_winner,
    "no_migration": no_migration,
}
