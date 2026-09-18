from pydantic import Field
from mercury.contracts.base import ContractModel

class BackfillCandidate(ContractModel):
    workload_id:str
    duration_units:float|None=Field(default=None,gt=0)
    resource_units:float=Field(gt=0)
    hard_requirements_satisfied:bool
    provenance_ids:tuple[str,...]

def select_backfill(candidates, *, protected_slack_units):
    candidates=tuple(candidates)
    if any(type(c) is not BackfillCandidate for c in candidates):
        raise ValueError("typed backfill candidates required")
    eligible=[c for c in candidates if c.duration_units is not None and c.duration_units<=protected_slack_units and c.hard_requirements_satisfied]
    return tuple(sorted((c.workload_id for c in eligible)))
