from mercury.compute_negotiator.contracts import ApprovalArtifact
from mercury.reasoning_budget.contracts import canonical_hash
def create_approval(*,offer,approver_authority_ref,accepted_changed_constraints,approval_generation):
    if set(accepted_changed_constraints)!=set(offer.changed_soft_constraints):
        raise ValueError("approval must exactly acknowledge changed constraints")
    body={"offer":offer.offer_id,"authority":approver_authority_ref,"changes":sorted(accepted_changed_constraints),"generation":approval_generation}
    fp=canonical_hash(body)
    return ApprovalArtifact(approval_id=canonical_hash({"approval":fp}),offer_id=offer.offer_id,
        approver_authority_ref=approver_authority_ref,accepted_changed_constraints=tuple(sorted(accepted_changed_constraints)),
        approval_generation=approval_generation,fingerprint=fp)
