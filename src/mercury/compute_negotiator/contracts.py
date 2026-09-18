from enum import Enum
from pydantic import Field, field_validator, model_validator
from mercury.contracts.base import ContractModel
from mercury.reasoning_budget.contracts import canonical_hash

class NegotiationOutcome(str,Enum):
    ACCEPT="ACCEPT"; COUNTEROFFER="COUNTEROFFER"; REJECT="REJECT"; UNKNOWN="UNKNOWN"
class NegotiationLifecycle(str,Enum):
    REQUESTED="REQUESTED"; EVALUATING="EVALUATING"; OFFERED="OFFERED"; COUNTEROFFERED="COUNTEROFFERED"; ACCEPTED="ACCEPTED"; REJECTED="REJECTED"; EXPIRED="EXPIRED"; REVOKED="REVOKED"; UNKNOWN="UNKNOWN"
class NegotiationEventType(str,Enum):
    REQUESTED="REQUESTED"; OFFERED="OFFERED"; APPROVED="APPROVED"; REJECTED="REJECTED"; EXPIRED="EXPIRED"; REVOKED="REVOKED"; COMMITTED="COMMITTED"

PROTECTED_CONSTRAINTS=frozenset(("quality","verification","safety","privacy","authorization","residency"))

def _text(value,name):
    if not isinstance(value,str) or not value.strip(): raise ValueError(f"{name} must be nonblank")
    return value

class ComputeNegotiationRequest(ContractModel):
    request_id:str; intelligence_slo_id:str; reasoning_budget_id:str
    placement_prediction_ids:tuple[str,...]; scheduling_decision_id:str
    resource_snapshot_generation:int=Field(ge=1); requested_quality_floor:float=Field(ge=0,le=1)

class ComputeOffer(ContractModel):
    offer_id:str; request_id:str; requested_quality_floor:float; proposed_quality_floor:float
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
        for name in ("offer_id","request_id","fingerprint"): _text(getattr(self,name),name)
        if not PROTECTED_CONSTRAINTS.issubset(self.protected_constraints):
            raise ValueError("all protected constraints must be preserved")
        if PROTECTED_CONSTRAINTS.intersection(self.changed_soft_constraints):
            raise ValueError("protected constraint change forbidden")
        payload={"request_id":self.request_id,"q":self.proposed_quality_floor,"requested_q":self.requested_quality_floor,
                 "latency":self.proposed_latency_ms,"resource":self.proposed_resource_units,
                 "placements":list(self.placement_candidate_ids),"spec":self.speculation_width,
                 "protected":list(self.protected_constraints),"changes":list(self.changed_soft_constraints),
                 "snapshot":self.resource_snapshot_generation,"lease":self.lease_until_generation}
        expected=canonical_hash(payload)
        if self.fingerprint!=expected or self.offer_id!=canonical_hash({"offer":expected}):
            raise ValueError("offer fingerprint mismatch")
        return self

class ApprovalArtifact(ContractModel):
    approval_id:str; offer_id:str; approver_authority_ref:str
    accepted_changed_constraints:tuple[str,...]; approval_generation:int=Field(ge=1); fingerprint:str
    @model_validator(mode="after")
    def integrity(self):
        for name in ("approval_id","offer_id","approver_authority_ref","fingerprint"): _text(getattr(self,name),name)
        body={"offer":self.offer_id,"authority":self.approver_authority_ref,
              "changes":list(self.accepted_changed_constraints),"generation":self.approval_generation}
        expected=canonical_hash(body)
        if self.fingerprint!=expected or self.approval_id!=canonical_hash({"approval":expected}):
            raise ValueError("approval fingerprint mismatch")
        return self

class NegotiationDecision(ContractModel):
    decision_id:str; outcome:NegotiationOutcome; offer_id:str|None=None
    explicit_approval_required:bool=False; reason_codes:tuple[str,...]=()

class ComputeAgreement(ContractModel):
    agreement_id:str; offer_id:str; approval_id:str|None=None
    resource_snapshot_generation:int; committed:bool; fingerprint:str
    @model_validator(mode="after")
    def integrity(self):
        body={"offer":self.offer_id,"approval":self.approval_id,"snapshot":self.resource_snapshot_generation}
        expected=canonical_hash(body)
        if not self.committed or self.fingerprint!=expected or self.agreement_id!=canonical_hash({"agreement":expected}):
            raise ValueError("agreement fingerprint mismatch")
        return self

class NegotiationRound(ContractModel):
    round_id:str; request_id:str; round_generation:int=Field(ge=1); previous_round_id:str|None=None
    lifecycle:NegotiationLifecycle; offer_ids:tuple[str,...]; resource_snapshot_generation:int=Field(ge=1)
    provenance_ids:tuple[str,...]; fingerprint:str
    @model_validator(mode="after")
    def integrity(self):
        body={"request_id":self.request_id,"round_generation":self.round_generation,
              "previous_round_id":self.previous_round_id,"lifecycle":self.lifecycle.value,
              "offer_ids":list(self.offer_ids),"resource_snapshot_generation":self.resource_snapshot_generation,
              "provenance_ids":list(self.provenance_ids)}
        expected=canonical_hash(body)
        if self.fingerprint!=expected or self.round_id!=canonical_hash({"negotiation_round":expected}):
            raise ValueError("round fingerprint mismatch")
        return self

class NegotiationHistoryEvent(ContractModel):
    event_id:str; request_id:str; sequence:int=Field(ge=1); event_type:NegotiationEventType
    artifact_id:str; generation:int=Field(ge=1); provenance_ids:tuple[str,...]; fingerprint:str
    @model_validator(mode="after")
    def integrity(self):
        body=self.model_dump(mode="json",exclude={"event_id","fingerprint"})
        expected=canonical_hash(body)
        if self.fingerprint!=expected or self.event_id!=canonical_hash({"negotiation_event":expected}):
            raise ValueError("history event fingerprint mismatch")
        return self
