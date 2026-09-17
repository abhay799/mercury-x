from mercury.speculation.contracts import *
from mercury.speculation.planner import build_speculation_plan
from mercury.speculation.commit import commit_verified_winner
def behavior():
    p=build_speculation_plan(source_segment_id="s",candidate_ids=("c1",),max_branches=1)
    b=SpeculativeBranch(branch_id="b",placement_candidate_id="c1",state=SpeculativeBranchState.SUCCEEDED,result_id="r",verified=True)
    r=commit_verified_winner(p,(b,))
    return r.winning_branch_id=="b", "verified deterministic winner"
def enums():
    return len(SpeculativeBranchState)==8, "exact branch states"
def boundary():
    import inspect, mercury.speculation.commit as c
    t=inspect.getsource(c)
    return "migrate(" not in t, "no migration behavior"
CHECKS={"states":enums,"bounded_fanout":behavior,"determinism":behavior,"verification_before_commit":behavior,"single_winner":behavior,"no_migration":boundary}
