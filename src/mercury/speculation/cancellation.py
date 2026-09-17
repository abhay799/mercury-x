from mercury.speculation.contracts import SpeculativeBranchState
from mercury.speculation.state import transition_branch
def cancel_losing_branches(branches,winning_branch_id):
    branches=tuple(branches)
    branch_ids=tuple(branch.branch_id for branch in branches)
    if len(branch_ids)!=len(set(branch_ids)):
        raise ValueError("duplicate branch id")
    if winning_branch_id not in branch_ids:
        raise ValueError("winning branch is not present")
    out=[]
    for b in sorted(branches,key=lambda branch:branch.branch_id):
        if b.branch_id==winning_branch_id:
            out.append(b); continue
        if b.state in {SpeculativeBranchState.PLANNED,SpeculativeBranchState.READY,SpeculativeBranchState.RUNNING}:
            out.append(transition_branch(b,SpeculativeBranchState.CANCELLED))
        elif b.state in {SpeculativeBranchState.SUCCEEDED,SpeculativeBranchState.FAILED}:
            out.append(transition_branch(b,SpeculativeBranchState.DISCARDED))
        else:
            out.append(b)
    return tuple(out)
