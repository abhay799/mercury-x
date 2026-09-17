import pytest

from mercury.disaggregated_execution.contracts import (
    ExecutionSegment,
    ExecutionSegmentState,
    ExecutionSegmentType,
)
from mercury.global_memory.contracts import GlobalMemoryNamespace
from mercury.placement.contracts import PlacementCandidate
from mercury.speculation.cancellation import cancel_losing_branches
from mercury.speculation.commit import commit_verified_winner
from mercury.speculation.contracts import (
    SpeculationPlan,
    SpeculativeBranch,
    SpeculativeBranchState,
)
from mercury.speculation.planner import build_speculation_plan
from mercury.speculation.state import transition_branch


def _plan() -> SpeculationPlan:
    return build_speculation_plan(
        source_segment_id="segment-1",
        candidate_ids=("candidate-1", "candidate-2"),
        max_branches=2,
    )


def _successful(branch_id: str, candidate_id: str, result_id: str) -> SpeculativeBranch:
    return SpeculativeBranch(
        branch_id=branch_id,
        placement_candidate_id=candidate_id,
        state=SpeculativeBranchState.SUCCEEDED,
        result_id=result_id,
        result_fingerprint=f"fingerprint-{result_id}",
        verification_evidence_id=f"evidence-{result_id}",
        verified=True,
    )


def _ready_segment(*, state: ExecutionSegmentState = ExecutionSegmentState.READY) -> ExecutionSegment:
    return ExecutionSegment(
        segment_id="segment-1",
        execution_plan_id="execution-plan-1",
        namespace_type=GlobalMemoryNamespace.PROJECT,
        namespace_id="project-1",
        segment_type=ExecutionSegmentType.DECODE,
        output_contract_id="output-contract-1",
        handoff_policy_id="handoff-policy-1",
        retry_policy_id="retry-policy-1",
        verification_policy_id="verification-policy-1",
        creation_sequence=1,
        execution_state=state,
    )


def _eligible_candidate(*, segment_id: str = "segment-1", eligible: bool = True) -> PlacementCandidate:
    return PlacementCandidate(
        candidate_id="candidate-1",
        segment_id=segment_id,
        topology_node_id="topology-node-1",
        hardware_profile_id="hardware-profile-1",
        eligible=eligible,
        reason_codes=("COMPATIBLE",),
    )


def test_contracts_reject_blank_identities_and_invalid_committed_branch() -> None:
    with pytest.raises(ValueError, match="source_segment_id"):
        SpeculationPlan(**(_plan().model_dump() | {"source_segment_id": " "}))

    with pytest.raises(ValueError, match="branch_id"):
        SpeculativeBranch(
            branch_id=" ",
            placement_candidate_id="candidate-1",
            state=SpeculativeBranchState.READY,
        )

    with pytest.raises(ValueError, match="verified result"):
        SpeculativeBranch(
            branch_id="branch-1",
            placement_candidate_id="candidate-1",
            state=SpeculativeBranchState.COMMITTED,
            result_id="result-1",
            result_fingerprint="result-fingerprint-1",
            verified=False,
        )


def test_commit_transition_cannot_clear_verification() -> None:
    with pytest.raises(ValueError, match="verification"):
        transition_branch(
            _successful("branch-1", "candidate-1", "result-1"),
            SpeculativeBranchState.COMMITTED,
            verified=False,
        )


def test_commit_rejects_nonmembers_duplicate_branch_ids_and_existing_commit() -> None:
    plan = _plan()
    winner = _successful("branch-1", "candidate-1", "result-1")
    unknown = _successful("branch-2", "unknown-candidate", "result-2")

    with pytest.raises(ValueError, match="plan candidate"):
        commit_verified_winner(plan, (winner, unknown))

    with pytest.raises(ValueError, match="duplicate branch"):
        commit_verified_winner(plan, (winner, winner))

    committed = SpeculativeBranch(
        branch_id="branch-2",
        placement_candidate_id="candidate-2",
        state=SpeculativeBranchState.COMMITTED,
        result_id="result-2",
        result_fingerprint="result-fingerprint-2",
        verification_evidence_id="evidence-result-2",
        verified=True,
    )
    with pytest.raises(ValueError, match="already committed"):
        commit_verified_winner(plan, (winner, committed))


def test_commit_materializes_iterable_once_before_computing_losers() -> None:
    plan = _plan()
    winner = _successful("branch-1", "candidate-1", "result-1")
    loser = SpeculativeBranch(
        branch_id="branch-2",
        placement_candidate_id="candidate-2",
        state=SpeculativeBranchState.FAILED,
    )

    result = commit_verified_winner(plan, (branch for branch in (loser, winner)))

    assert result.winning_branch_id == "branch-1"
    assert result.losing_branch_ids == ("branch-2",)


def test_cancellation_rejects_unknown_winner_and_is_canonical() -> None:
    first = SpeculativeBranch(
        branch_id="branch-1",
        placement_candidate_id="candidate-1",
        state=SpeculativeBranchState.READY,
    )
    second = SpeculativeBranch(
        branch_id="branch-2",
        placement_candidate_id="candidate-2",
        state=SpeculativeBranchState.RUNNING,
    )

    with pytest.raises(ValueError, match="winning branch"):
        cancel_losing_branches((first, second), "missing")

    forward = cancel_losing_branches((first, second), "branch-1")
    reverse = cancel_losing_branches((second, first), "branch-1")
    assert forward == reverse
    assert tuple(branch.branch_id for branch in forward) == ("branch-1", "branch-2")
    assert cancel_losing_branches(forward, "branch-1") == forward


def test_typed_plan_preserves_ready_phase12_segment_and_exact_eligible_phase15_candidates() -> None:
    segment = _ready_segment()
    candidate = _eligible_candidate()

    plan = build_speculation_plan(
        source_segment=segment,
        placement_candidates=(candidate,),
        max_branches=1,
    )

    assert plan.source_execution_plan_id == segment.execution_plan_id
    assert plan.namespace_type == segment.namespace_type
    assert plan.namespace_id == segment.namespace_id
    assert plan.source_segment_id == segment.segment_id
    assert plan.placement_candidate_ids == (candidate.candidate_id,)
    assert plan.candidate_fingerprints[0][0] == candidate.candidate_id

    with pytest.raises(ValueError, match="READY"):
        build_speculation_plan(
            source_segment=_ready_segment(state=ExecutionSegmentState.RUNNING),
            placement_candidates=(candidate,),
            max_branches=1,
        )
    with pytest.raises(ValueError, match="eligible"):
        build_speculation_plan(
            source_segment=segment,
            placement_candidates=(_eligible_candidate(eligible=False),),
            max_branches=1,
        )
    with pytest.raises(ValueError, match="segment"):
        build_speculation_plan(
            source_segment=segment,
            placement_candidates=(_eligible_candidate(segment_id="other-segment"),),
            max_branches=1,
        )


def test_typed_commit_rejects_stale_branch_generation_and_preserves_verified_provenance() -> None:
    plan = build_speculation_plan(
        source_segment=_ready_segment(),
        placement_candidates=(_eligible_candidate(),),
        max_branches=1,
    )
    candidate_fingerprint = plan.candidate_fingerprints[0][1]
    branch = SpeculativeBranch(
        branch_id="branch-1",
        placement_candidate_id="candidate-1",
        state=SpeculativeBranchState.SUCCEEDED,
        result_id="result-1",
        result_fingerprint="result-fingerprint-1",
        verification_evidence_id="verification-evidence-1",
        speculation_plan_id=plan.speculation_plan_id,
        source_segment_id=plan.source_segment_id,
        plan_fingerprint=plan.fingerprint,
        candidate_fingerprint=candidate_fingerprint,
        verified=True,
    )

    result = commit_verified_winner(plan, (branch,))

    assert result.source_segment_id == plan.source_segment_id
    assert result.source_execution_plan_id == plan.source_execution_plan_id
    assert result.verification_evidence_id == branch.verification_evidence_id
    assert result.winning_result_fingerprint == branch.result_fingerprint

    with pytest.raises(ValueError, match="stale"):
        commit_verified_winner(
            plan,
            (branch.model_copy(update={"plan_fingerprint": "stale-generation"}),),
        )


def test_logical_commit_is_exactly_once_idempotent_for_the_same_verified_branch_set() -> None:
    plan = _plan()
    winner = _successful("branch-1", "candidate-1", "result-1")
    failed = SpeculativeBranch(
        branch_id="branch-2", placement_candidate_id="candidate-2", state=SpeculativeBranchState.FAILED
    )
    first = commit_verified_winner(plan, (winner, failed))
    second = commit_verified_winner(plan, (winner, failed))
    assert second == first
    assert second.result_fingerprint == first.result_fingerprint
