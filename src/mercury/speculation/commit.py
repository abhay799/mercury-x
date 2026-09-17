from mercury.speculation.contracts import SpeculativeBranchState,SpeculativeResult,sh
def commit_verified_winner(plan,branches):
    eligible=[b for b in branches if b.state is SpeculativeBranchState.SUCCEEDED and b.verified and b.result_id]
    if not eligible: raise ValueError("no verified successful branch")
    winner=sorted(eligible,key=lambda b:b.branch_id)[0]
    losers=tuple(sorted(b.branch_id for b in branches if b.branch_id!=winner.branch_id))
    fp=sh({"plan":plan.speculation_plan_id,"winner":winner.branch_id,"result":winner.result_id,"losers":losers})
    return SpeculativeResult(speculation_plan_id=plan.speculation_plan_id,winning_branch_id=winner.branch_id,
        committed_result_id=winner.result_id,losing_branch_ids=losers,result_fingerprint=fp)
