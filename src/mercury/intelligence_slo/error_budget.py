from mercury.contracts.base import ContractModel
from pydantic import Field
class ErrorBudget(ContractModel):
    metric_id:str; allowed_violations:int=Field(ge=0); consumed_violations:int=Field(ge=0); window_generations:int=Field(ge=1)
    provenance_ids:tuple[str,...]
    @property
    def exhausted(self): return self.consumed_violations>=self.allowed_violations
def consume_error_budget(budget,count=1):
    if count<0: raise ValueError("count must be nonnegative")
    return budget.model_copy(update={"consumed_violations":budget.consumed_violations+count})

def build_error_budget(*,metric_id,allowed_violations,window_generations,provenance_ids):
    protected=metric_id.startswith(("safety.","privacy.","authorization.","residency."))
    allowed=0 if allowed_violations is None else allowed_violations
    if protected and allowed!=0: raise ValueError("protected metric has zero violation budget")
    return ErrorBudget(metric_id=metric_id,allowed_violations=allowed,consumed_violations=0,
                       window_generations=window_generations,provenance_ids=tuple(sorted(provenance_ids)))
