from enum import Enum
from pydantic import Field, model_validator
from mercury.contracts.base import ContractModel
from mercury.reasoning_budget.contracts import canonical_hash

class NegotiationOutcome(str,Enum):
    ACCEPT="ACCEPT"; COUNTEROFFER="COUNTEROFFER"; REJECT="REJECT"; UNKNOWN="UNKNOWN"
class NegotiationLifecycle(str,Enum):
    REQUESTED="REQUESTED"; EVALUATING="EVALUATING"; OFFERED="OFFERED"; COUNTEROFFERED="COUNTEROFFERED"; ACCEPTED="ACCEPTED"; REJECTED="REJECTED"; EXPIRED="EXPIRED"; REVOKED="REVOKED"; UNKNOWN="UNKNOWN"

class ComputeNegotiationRequest(ContractModel):
    request_id:str; intelligence_slo_id:str; reasoning_budget_id:str
    placement_prediction_ids:tuple[str,...]; scheduling_decision_id:str
    resource_snapshot_generation:int=Field(ge=1); requested_quality_floor:float=Field(ge=0,le=1)

class ComputeOffer(ContractModel):
    offer_id:str; requested_quality_floor:float; proposed_quality_floor:float
    proposed_latency_ms:int=Field(ge=1); proposed_resource_units:float=Field(gt=0)
    placement_candidate_ids:tuple[str,...]; speculation_width:int=Field(ge=1)
    protected_constraints:tuple[str,...]; changed_soft_constraints:tuple[str,...]=()
    resource_snapshot_generation:int=Field(ge=1); lease_until_generation:int=Field(ge=1)
    reason_codes:tuple[str,...]=(); fingerprint:str
    @model_validator(mode="after")
    def no_quality_reduction(self):
        if self.proposed_quality_floor < self.requested_quality_floor:
            raise ValueError("quality reduction forbidden")
        if self.lease_until_generation < self.resource_snapshot_generation:
            raise ValueError("invalid offer lease")
        return self

class ApprovalArtifact(ContractModel):
    approval_id:str; offer_id:str; approver_authority_ref:str
    accepted_changed_constraints:tuple[str,...]; approval_generation:int=Field(ge=1); fingerprint:str

class NegotiationDecision(ContractModel):
    decision_id:str; outcome:NegotiationOutcome; offer_id:str|None=None
    explicit_approval_required:bool=False; reason_codes:tuple[str,...]=()

class ComputeAgreement(ContractModel):
    agreement_id:str; offer_id:str; approval_id:str|None=None
    resource_snapshot_generation:int; committed:bool; fingerprint:str
