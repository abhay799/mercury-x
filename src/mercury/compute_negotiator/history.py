from pydantic import model_validator
from mercury.contracts.base import ContractModel
from mercury.compute_negotiator.contracts import NegotiationHistoryEvent
from mercury.reasoning_budget.contracts import canonical_hash
class NegotiationHistory(ContractModel):
    request_id:str; events:tuple[NegotiationHistoryEvent,...]; fingerprint:str
    @model_validator(mode="after")
    def integrity(self):
        if tuple(e.sequence for e in self.events)!=tuple(range(1,len(self.events)+1)): raise ValueError("history sequence gap")
        if any(e.request_id!=self.request_id for e in self.events): raise ValueError("history request mismatch")
        expected=canonical_hash({"request_id":self.request_id,"events":[e.event_id for e in self.events]})
        if self.fingerprint!=expected: raise ValueError("history fingerprint mismatch")
        return self
def append_history_event(history,*,event_type,artifact_id,generation,provenance_ids):
    body={"request_id":history.request_id,"sequence":len(history.events)+1,"event_type":event_type.value,
          "artifact_id":artifact_id,"generation":generation,"provenance_ids":list(provenance_ids)}
    fp=canonical_hash(body)
    event=NegotiationHistoryEvent(event_id=canonical_hash({"negotiation_event":fp}),fingerprint=fp,**body)
    events=history.events+(event,)
    return NegotiationHistory(request_id=history.request_id,events=events,
        fingerprint=canonical_hash({"request_id":history.request_id,"events":[e.event_id for e in events]}))
def empty_history(request_id="legacy-request"):
    return NegotiationHistory(request_id=request_id,events=(),fingerprint=canonical_hash({"request_id":request_id,"events":[]}))
