from mercury.contracts.base import ContractModel
from mercury.reasoning_budget.contracts import canonical_hash

class CounterfactualBudgetScenario(ContractModel):
    scenario_id:str
    reasoning_steps:int
    verification_depth:int
    speculation_width:int
    latency_ceiling_ms:int
    advisory_only:bool=True

def simulate_budget_alternatives(request):
    variants=[
        (request.max_reasoning_steps,request.verification_depth_min,request.max_speculative_branches,request.latency_ceiling_ms),
        (request.max_reasoning_steps+1,request.verification_depth_min,request.max_speculative_branches,request.latency_ceiling_ms),
        (request.max_reasoning_steps,request.verification_depth_min+1,request.max_speculative_branches,request.latency_ceiling_ms),
        (request.max_reasoning_steps,request.verification_depth_min,min(request.max_speculative_branches+1,8),request.latency_ceiling_ms),
        (request.max_reasoning_steps,request.verification_depth_min,request.max_speculative_branches,request.latency_ceiling_ms+250),
    ]
    out=[]
    for v in sorted(set(variants)):
        out.append(CounterfactualBudgetScenario(
            scenario_id=canonical_hash({"scenario":v}), reasoning_steps=v[0],verification_depth=v[1],
            speculation_width=v[2],latency_ceiling_ms=v[3]))
    return tuple(out)
