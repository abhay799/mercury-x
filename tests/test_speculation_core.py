import pytest
from mercury.speculation.contracts import *
from mercury.speculation.planner import build_speculation_plan
from mercury.speculation.commit import commit_verified_winner
def test_plan_is_bounded_and_winner_requires_verification():
    p=build_speculation_plan(source_segment_id="s",candidate_ids=("c2","c1"),max_branches=2)
    assert p.placement_candidate_ids==("c1","c2")
    b1=SpeculativeBranch(branch_id="b1",placement_candidate_id="c1",state=SpeculativeBranchState.SUCCEEDED,result_id="r1",verified=True)
    b2=SpeculativeBranch(branch_id="b2",placement_candidate_id="c2",state=SpeculativeBranchState.SUCCEEDED,result_id="r2",verified=False)
    r=commit_verified_winner(p,(b2,b1))
    assert r.winning_branch_id=="b1"
    with pytest.raises(ValueError):
        build_speculation_plan(source_segment_id="s",candidate_ids=tuple(f"c{i}" for i in range(9)),max_branches=8)
