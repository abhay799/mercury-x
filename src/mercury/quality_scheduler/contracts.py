from enum import Enum
from pydantic import Field, field_validator
from mercury.contracts.base import ContractModel
from mercury.reasoning_budget.contracts import canonical_hash

class AdmissionState(str,Enum):
    ADMIT="ADMIT"; DEFER="DEFER"; REJECT="REJECT"; UNKNOWN="UNKNOWN"
class PriorityClass(str,Enum):
    CRITICAL="CRITICAL"; HIGH="HIGH"; NORMAL="NORMAL"; LOW="LOW"

class SchedulingRequest(ContractModel):
    workload_id:str; segment_id:str; placement_candidate_ids:tuple[str,...]; reasoning_budget_id:str
    requirement_interface_id:str; arrival_generation:int=Field(ge=0); queue_class:str="default"
    fairness_weight:float=Field(default=1.0,gt=0)
    @field_validator("placement_candidate_ids")
    @classmethod
    def uniq(cls,v):
        if len(v)!=len(set(v)): raise ValueError("duplicate placement candidate")
        return tuple(sorted(v))

class SchedulingFeatures(ContractModel):
    deadline_pressure:float=Field(ge=0,le=1); quality_risk:float=Field(ge=0,le=1)
    verification_pressure:float=Field(ge=0,le=1); uncertainty:float=Field(ge=0,le=1)
    budget_pressure:float=Field(ge=0,le=1); placement_confidence:float=Field(ge=0,le=1)
    logical_age:int=Field(ge=0); fairness_weight:float=Field(gt=0)
    resource_pressure:float=Field(ge=0,le=1); locality_score:float=Field(ge=0,le=1)
    fragmentation_cost:float=Field(ge=0,le=1)

class SchedulingDecision(ContractModel):
    decision_id:str; workload_id:str; admission_state:AdmissionState; priority_class:PriorityClass
    rank_score:float; selected_candidate_ids:tuple[str,...]=(); reason_codes:tuple[str,...]=()

class PreemptionIntent(ContractModel):
    victim_workload_id:str; challenger_workload_id:str; allowed:bool; reason_codes:tuple[str,...]=()

class GangRequirement(ContractModel):
    gang_id:str; required_candidate_ids:tuple[str,...]
