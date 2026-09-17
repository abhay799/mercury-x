import hashlib,json
from enum import Enum
from pydantic import Field, model_validator
from mercury.contracts.base import ContractModel
MAX_SPECULATIVE_BRANCHES=8
class SpeculativeBranchState(str,Enum):
    PLANNED="PLANNED"; READY="READY"; RUNNING="RUNNING"; SUCCEEDED="SUCCEEDED"; FAILED="FAILED"; CANCELLED="CANCELLED"; COMMITTED="COMMITTED"; DISCARDED="DISCARDED"
class SpeculationPlan(ContractModel):
    speculation_plan_id:str; source_segment_id:str; placement_candidate_ids:tuple[str,...]
    max_branches:int=Field(ge=1,le=MAX_SPECULATIVE_BRANCHES)
    verification_policy_id:str; commit_policy_id:str; cancellation_policy_id:str; fingerprint:str
    @model_validator(mode="after")
    def bounded(self):
        if len(self.placement_candidate_ids)>self.max_branches: raise ValueError("branch count exceeds plan bound")
        if len(self.placement_candidate_ids)!=len(set(self.placement_candidate_ids)): raise ValueError("duplicate candidate")
        return self
class SpeculativeBranch(ContractModel):
    branch_id:str; placement_candidate_id:str; state:SpeculativeBranchState; result_id:str|None=None; verified:bool=False
class SpeculativeResult(ContractModel):
    speculation_plan_id:str; winning_branch_id:str; committed_result_id:str
    losing_branch_ids:tuple[str,...]; result_fingerprint:str
def sh(payload): return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()
