from mercury.contracts.base import ContractModel
from mercury.reasoning_budget.contracts import canonical_hash
class NegotiationHistory(ContractModel):
    event_ids:tuple[str,...]; fingerprint:str
def append_history(history,event_id):
    ids=history.event_ids+(event_id,)
    return NegotiationHistory(event_ids=ids,fingerprint=canonical_hash({"events":ids}))
def empty_history():
    return NegotiationHistory(event_ids=(),fingerprint=canonical_hash({"events":[]}))
