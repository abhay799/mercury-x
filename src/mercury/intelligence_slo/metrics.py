from enum import Enum
from mercury.contracts.base import ContractModel
from pydantic import field_validator
from mercury.reasoning_budget.contracts import canonical_hash
class ThresholdDirection(str,Enum):
    MINIMUM="MINIMUM"; MAXIMUM="MAXIMUM"; EXACT="EXACT"
class MetricDefinition(ContractModel):
    metric_id:str; metric_version:str; semantic_meaning:str; unit:str; evaluator_id:str; evaluator_version:str
    threshold_direction:ThresholdDirection; aggregation_rule:str; workload_classes:tuple[str,...]
    calibration_state:str; calibration_artifact_id:str|None=None; provenance_ids:tuple[str,...]
    @field_validator("workload_classes","provenance_ids")
    @classmethod
    def canonical(cls,v,info):
        if not v or any(not x.strip() for x in v) or len(v)!=len(set(v)): raise ValueError(f"invalid {info.field_name}")
        return tuple(sorted(v))
class MetricRegistry:
    def __init__(self,metrics=(),generation=1):
        items=tuple(sorted(metrics,key=lambda metric:metric.metric_id))
        if len({m.metric_id for m in items})!=len(items): raise ValueError("duplicate metric id")
        self._metrics={m.metric_id:m for m in items}; self.generation=generation
        self.fingerprint=canonical_hash({"generation":generation,"metrics":[m.model_dump(mode="json") for m in items]})
    def get(self,metric_id):
        if metric_id not in self._metrics: raise ValueError("undefined metric")
        return self._metrics[metric_id]
