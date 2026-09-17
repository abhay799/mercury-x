from mercury.speculation.contracts import SpeculativeBranch,SpeculativeBranchState
_ALLOWED={
SpeculativeBranchState.PLANNED:{SpeculativeBranchState.READY,SpeculativeBranchState.CANCELLED},
SpeculativeBranchState.READY:{SpeculativeBranchState.RUNNING,SpeculativeBranchState.CANCELLED},
SpeculativeBranchState.RUNNING:{SpeculativeBranchState.SUCCEEDED,SpeculativeBranchState.FAILED,SpeculativeBranchState.CANCELLED},
SpeculativeBranchState.SUCCEEDED:{SpeculativeBranchState.COMMITTED,SpeculativeBranchState.DISCARDED},
SpeculativeBranchState.FAILED:{SpeculativeBranchState.DISCARDED},
SpeculativeBranchState.CANCELLED:{SpeculativeBranchState.DISCARDED},
}
def transition_branch(branch,target,*,result_id=None,verified=None):
    if target not in _ALLOWED.get(branch.state,set()): raise ValueError("forbidden branch transition")
    if target is SpeculativeBranchState.COMMITTED and not branch.verified: raise ValueError("verification required before commit")
    p=branch.model_dump(); p["state"]=target
    if result_id is not None: p["result_id"]=result_id
    if verified is not None: p["verified"]=verified
    return SpeculativeBranch(**p)
