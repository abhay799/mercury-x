from enum import Enum
from mercury.contracts.base import ContractModel
class ThresholdDirection(str,Enum):
    MINIMUM="MINIMUM"; MAXIMUM="MAXIMUM"; EXACT="EXACT"
class MetricDefinition(ContractModel):
    metric_id:str; semantic_meaning:str; unit:str; evaluator_id:str
    threshold_direction:ThresholdDirection; aggregation_rule:str; workload_classes:tuple[str,...]=()
class MetricRegistry:
    def __init__(self,metrics=()):
        self._metrics={}
        for m in metrics:self.register(m)
    def register(self,m):
        if m.metric_id in self._metrics: raise ValueError("duplicate metric id")
        self._metrics[m.metric_id]=m
    def get(self,metric_id):
        if metric_id not in self._metrics: raise ValueError("undefined metric")
        return self._metrics[metric_id]
