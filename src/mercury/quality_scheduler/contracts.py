from enum import Enum
from pydantic import Field, field_validator, model_validator
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
    queue_generation:int=Field(ge=1)
    tenant_id:str
    workload_class:str
    required_quality_floor:float=Field(ge=0,le=1)
    required_resource_units:float=Field(gt=0)
    reasoning_budget_generation:int=Field(ge=1)
    placement_generation:int=Field(ge=1)
    provenance_ids:tuple[str,...]
    @field_validator("placement_candidate_ids")
    @classmethod
    def uniq(cls,v):
        if len(v)!=len(set(v)): raise ValueError("duplicate placement candidate")
        return tuple(sorted(v))
    @field_validator("workload_id","segment_id","reasoning_budget_id","requirement_interface_id","tenant_id","workload_class","queue_class")
    @classmethod
    def req_text(cls,v):
        if not isinstance(v,str) or not v.strip(): raise ValueError("scheduling identity must be nonblank")
        return v
    @field_validator("provenance_ids")
    @classmethod
    def provenance(cls,v):
        if not v or any(not item.strip() for item in v) or len(v)!=len(set(v)): raise ValueError("invalid scheduling provenance")
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
    queue_generation:int=Field(ge=1)
    decision_generation:int=Field(ge=1)
    previous_decision_id:str|None=None
    required_quality_floor:float=Field(ge=0,le=1)
    provenance_ids:tuple[str,...]
    fingerprint:str
    @model_validator(mode="after")
    def integrity(self):
        if len(self.selected_candidate_ids)!=len(set(self.selected_candidate_ids)): raise ValueError("selected candidates contain duplicates")
        payload={"workload_id":self.workload_id,"admission_state":self.admission_state.value,
                 "priority_class":self.priority_class.value,"rank_score":self.rank_score,
                 "selected_candidate_ids":list(self.selected_candidate_ids),"queue_generation":self.queue_generation,
                 "decision_generation":self.decision_generation,"previous_decision_id":self.previous_decision_id,
                 "required_quality_floor":self.required_quality_floor,"provenance_ids":list(self.provenance_ids)}
        expected=canonical_hash(payload)
        if self.fingerprint!=expected or self.decision_id!=canonical_hash({"scheduling_decision":expected}): raise ValueError("scheduling decision identity mismatch")
        return self

class PreemptionIntent(ContractModel):
    victim_workload_id:str; challenger_workload_id:str; allowed:bool; reason_codes:tuple[str,...]=()

class GangRequirement(ContractModel):
    gang_id:str; required_candidate_ids:tuple[str,...]
    required_topology_domain:str
    simultaneous:bool=True
    provenance_ids:tuple[str,...]

class SchedulingAdmissionEvidence(ContractModel):
    hardware_compatible:bool
    topology_compatible:bool
    placement_eligible:bool
    reasoning_budget_valid:bool
    hard_requirements_satisfied:bool
    evidence_sufficient:bool
    available_resource_units:float=Field(ge=0)
    required_resource_units:float=Field(gt=0)
    source_ids:tuple[str,...]

class FairnessState(ContractModel):
    workload_id:str
    tenant_id:str
    workload_class:str
    logical_age:int=Field(ge=0)
    queue_generation:int=Field(ge=1)
    fingerprint:str
