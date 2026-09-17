from mercury.speculation.contracts import (
    SpeculationPlan,
    SpeculativeBranch,
    SpeculativeBranchState,
    SpeculativeResult,
    sh,
    speculative_result_payload,
)


def _validated_plan(plan) -> SpeculationPlan:
    if type(plan) is not SpeculationPlan:
        raise ValueError("commit requires a typed speculation plan")
    return SpeculationPlan.model_validate(plan.model_dump())


def _validated_branches(branches) -> tuple[SpeculativeBranch, ...]:
    materialized = tuple(branches)
    if any(type(branch) is not SpeculativeBranch for branch in materialized):
        raise ValueError("commit requires typed speculative branches")
    return tuple(SpeculativeBranch.model_validate(branch.model_dump()) for branch in materialized)


def commit_verified_winner(plan, branches):
    plan = _validated_plan(plan)
    branches = _validated_branches(branches)
    branch_ids = tuple(branch.branch_id for branch in branches)
    if len(branch_ids) != len(set(branch_ids)):
        raise ValueError("duplicate branch id")
    if any(branch.state is SpeculativeBranchState.COMMITTED for branch in branches):
        raise ValueError("plan already committed")

    candidate_ids = tuple(branch.placement_candidate_id for branch in branches)
    if set(candidate_ids) != set(plan.placement_candidate_ids) or len(candidate_ids) != len(plan.placement_candidate_ids):
        raise ValueError("branches must cover the plan candidate set exactly once")
    candidate_fingerprints = dict(plan.candidate_fingerprints)
    typed_plan = plan.source_execution_plan_id is not None
    for branch in branches:
        branch_context = (
            branch.speculation_plan_id,
            branch.source_segment_id,
            branch.plan_fingerprint,
            branch.candidate_fingerprint,
        )
        if typed_plan and any(value is None for value in branch_context):
            raise ValueError("typed plan requires branch generation provenance")
        if any(value is not None for value in branch_context) and (
            branch.speculation_plan_id != plan.speculation_plan_id
            or branch.source_segment_id != plan.source_segment_id
            or branch.plan_fingerprint != plan.fingerprint
            or branch.candidate_fingerprint != candidate_fingerprints[branch.placement_candidate_id]
        ):
            raise ValueError("stale branch generation does not match speculation plan")

    eligible = [
        branch
        for branch in branches
        if branch.state is SpeculativeBranchState.SUCCEEDED
        and branch.verified
        and branch.result_id
        and branch.result_fingerprint
        and branch.verification_evidence_id
    ]
    if not eligible:
        raise ValueError("no verified successful branch")
    winner = sorted(eligible, key=lambda branch: branch.branch_id)[0]
    losers = tuple(sorted(branch.branch_id for branch in branches if branch.branch_id != winner.branch_id))
    values = {
        "speculation_plan_id": plan.speculation_plan_id,
        "source_segment_id": plan.source_segment_id,
        "source_execution_plan_id": plan.source_execution_plan_id,
        "namespace_type": plan.namespace_type,
        "namespace_id": plan.namespace_id,
        "plan_fingerprint": plan.fingerprint,
        "winning_branch_id": winner.branch_id,
        "committed_result_id": winner.result_id,
        "winning_result_fingerprint": winner.result_fingerprint,
        "verification_evidence_id": winner.verification_evidence_id,
        "losing_branch_ids": losers,
    }
    fingerprint_payload = {
        **values,
        "namespace_type": values["namespace_type"].value if values["namespace_type"] else None,
    }
    return SpeculativeResult(
        result_fingerprint=sh(fingerprint_payload),
        **values,
    )
