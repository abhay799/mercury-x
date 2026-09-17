from mercury.contracts.base import ContractModel
from pydantic import Field
class ErrorBudget(ContractModel):
    metric_id:str; allowed_violations:int=Field(ge=0); consumed_violations:int=Field(ge=0); window_generations:int=Field(ge=1)
    @property
    def exhausted(self): return self.consumed_violations>=self.allowed_violations
def consume_error_budget(budget,count=1):
    if count<0: raise ValueError("count must be nonnegative")
    return budget.model_copy(update={"consumed_violations":budget.consumed_violations+count})
