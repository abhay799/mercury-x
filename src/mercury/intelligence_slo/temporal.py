from mercury.contracts.base import ContractModel
from pydantic import Field, model_validator
class TemporalTarget(ContractModel):
    percentile:float|None=Field(default=None,gt=0,le=100)
    window_generations:int|None=Field(default=None,ge=1)
    burst_limit:int|None=Field(default=None,ge=1)
    @model_validator(mode="after")
    def at_least_one(self):
        if self.percentile is None and self.window_generations is None and self.burst_limit is None:
            raise ValueError("temporal target requires semantics")
        return self
