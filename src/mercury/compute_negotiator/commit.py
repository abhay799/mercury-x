from mercury.compute_negotiator.contracts import ComputeAgreement
from mercury.compute_negotiator.lease import offer_is_valid
from mercury.reasoning_budget.contracts import canonical_hash
def commit_agreement(*,offer,approval,current_generation,current_resource_snapshot_generation,authorization_valid,hard_constraints_still_hold):
    ok,reason=offer_is_valid(offer,current_generation=current_generation,current_resource_snapshot_generation=current_resource_snapshot_generation)
    if not ok: raise ValueError(reason)
    if not authorization_valid: raise ValueError("authorization invalid")
    if not hard_constraints_still_hold: raise ValueError("hard constraint drift")
    if offer.changed_soft_constraints and approval is None: raise ValueError("explicit approval required")
    if approval is not None and approval.offer_id!=offer.offer_id: raise ValueError("approval/offer mismatch")
    body={"offer":offer.offer_id,"approval":None if approval is None else approval.approval_id,"snapshot":current_resource_snapshot_generation}
    fp=canonical_hash(body)
    return ComputeAgreement(agreement_id=canonical_hash({"agreement":fp}),offer_id=offer.offer_id,
        approval_id=None if approval is None else approval.approval_id,
        resource_snapshot_generation=current_resource_snapshot_generation,committed=True,fingerprint=fp)
