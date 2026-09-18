from mercury.compute_negotiator.contracts import ComputeAgreement
from mercury.compute_negotiator.lease import offer_is_valid
from mercury.reasoning_budget.contracts import canonical_hash
from threading import Lock

class AgreementCommitLedger:
    def __init__(self): self._committed=set(); self._lock=Lock()
    def claim(self,offer_id):
        with self._lock:
            if offer_id in self._committed: raise ValueError("offer already committed")
            self._committed.add(offer_id)

def commit_agreement(*,offer,approval,current_generation,current_resource_snapshot_generation,authorization_valid,hard_constraints_still_hold,ledger=None):
    ok,reason=offer_is_valid(offer,current_generation=current_generation,current_resource_snapshot_generation=current_resource_snapshot_generation)
    if not ok: raise ValueError(reason)
    if not authorization_valid: raise ValueError("authorization invalid")
    if not hard_constraints_still_hold: raise ValueError("hard constraint drift")
    if offer.changed_soft_constraints and approval is None: raise ValueError("explicit approval required")
    if approval is not None:
        if approval.offer_id!=offer.offer_id: raise ValueError("approval/offer mismatch")
        if approval.approval_generation!=current_generation: raise ValueError("approval generation mismatch")
        if set(approval.accepted_changed_constraints)!=set(offer.changed_soft_constraints): raise ValueError("approval constraint mismatch")
    if ledger is not None: ledger.claim(offer.offer_id)
    body={"offer":offer.offer_id,"approval":None if approval is None else approval.approval_id,"snapshot":current_resource_snapshot_generation}
    fp=canonical_hash(body)
    return ComputeAgreement(agreement_id=canonical_hash({"agreement":fp}),offer_id=offer.offer_id,
        approval_id=None if approval is None else approval.approval_id,
        resource_snapshot_generation=current_resource_snapshot_generation,committed=True,fingerprint=fp)
