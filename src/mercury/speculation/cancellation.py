from mercury.speculation.contracts import SpeculativeBranchState
from mercury.speculation.state import transition_branch
def cancel_losing_branches(branches,winning_branch_id):
    out=[]
    for b in branches:
        if b.branch_id==winning_branch_id:
            out.append(b); continue
        if b.state in {SpeculativeBranchState.PLANNED,SpeculativeBranchState.READY,SpeculativeBranchState.RUNNING}:
            out.append(transition_branch(b,SpeculativeBranchState.CANCELLED))
        elif b.state in {SpeculativeBranchState.SUCCEEDED,SpeculativeBranchState.FAILED,SpeculativeBranchState.CANCELLED}:
            out.append(transition_branch(b,SpeculativeBranchState.DISCARDED))
        else:
            out.append(b)
    return tuple(out)
