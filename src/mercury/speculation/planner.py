from mercury.speculation.contracts import SpeculationPlan,sh
def build_speculation_plan(*,source_segment_id,candidate_ids,max_branches,verification_policy_id="verify",commit_policy_id="first_verified",cancellation_policy_id="cancel_losers"):
    ids=tuple(sorted(candidate_ids))
    body={"source_segment_id":source_segment_id,"candidate_ids":ids,"max_branches":max_branches,
          "verification_policy_id":verification_policy_id,"commit_policy_id":commit_policy_id,"cancellation_policy_id":cancellation_policy_id}
    fp=sh(body)
    return SpeculationPlan(speculation_plan_id=sh({"plan":fp}),source_segment_id=source_segment_id,
        placement_candidate_ids=ids,max_branches=max_branches,verification_policy_id=verification_policy_id,
        commit_policy_id=commit_policy_id,cancellation_policy_id=cancellation_policy_id,fingerprint=fp)
