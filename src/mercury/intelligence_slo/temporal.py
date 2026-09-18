from mercury.contracts.base import ContractModel
from pydantic import Field, model_validator
from mercury.reasoning_budget.contracts import canonical_hash
class TemporalTarget(ContractModel):
    percentile:float|None=Field(default=None,gt=0,le=100)
    window_generations:int|None=Field(default=None,ge=1)
    burst_limit:int|None=Field(default=None,ge=1)
    availability_window_generations:int|None=Field(default=None,ge=1)
    provenance_ids:tuple[str,...]
    fingerprint:str|None=None
    @model_validator(mode="before")
    @classmethod
    def populate_fingerprint(cls,values):
        values=dict(values)
        if values.get("fingerprint") is None:
            payload={
                "percentile":None if values.get("percentile") is None else float(values["percentile"]),
                "window_generations":values.get("window_generations"),
                "burst_limit":values.get("burst_limit"),
                "availability_window_generations":values.get("availability_window_generations"),
                "provenance_ids":list(values.get("provenance_ids",())),
            }
            values["fingerprint"]=canonical_hash(payload)
        return values
    @model_validator(mode="after")
    def at_least_one(self):
        if self.percentile is None and self.window_generations is None and self.burst_limit is None and self.availability_window_generations is None:
            raise ValueError("temporal target requires semantics")
        expected=canonical_hash(self.model_dump(exclude={"fingerprint"}))
        if self.fingerprint!=expected: raise ValueError("temporal target fingerprint mismatch")
        return self
