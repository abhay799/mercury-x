from mercury.intelligence_slo.metrics import *
from mercury.intelligence_slo.contracts import *
from mercury.intelligence_slo.compiler import compile_sla
from mercury.intelligence_slo.temporal import TemporalTarget
from mercury.intelligence_slo.error_budget import ErrorBudget
def registry():
    r=MetricRegistry((MetricDefinition(metric_id="quality.primary",semantic_meaning="quality",unit="score",evaluator_id="e",threshold_direction=ThresholdDirection.MINIMUM,aggregation_rule="mean"),))
    return r.get("quality.primary").metric_id=="quality.primary","metric registry executable"
def compile_behavior():
    reg=MetricRegistry((MetricDefinition(metric_id="quality.primary",semantic_meaning="quality",unit="score",evaluator_id="e",threshold_direction=ThresholdDirection.MINIMUM,aggregation_rule="mean"),))
    req=IntelligenceRequirement(requirement_id="q",metric_id="quality.primary",kind=ConstraintKind.HARD,threshold=.9,operator=">=",source_id="app")
    slo,_=compile_sla(ApplicationSLA(sla_id="s",requirements=(req,)),reg)
    return not slo.degradation_allowed and slo.status is CompilationStatus.VALID,"compiler preserves hard quality"
def temporal():
    return TemporalTarget(percentile=99,window_generations=10).percentile==99,"temporal semantics executable"
def error_budget():
    return not ErrorBudget(metric_id="m",allowed_violations=1,consumed_violations=0,window_generations=10).exhausted,"error budget executable"
CHECKS={"metric_registry":registry,"constraint_typing":compile_behavior,"policy_hierarchy":compile_behavior,"temporal_semantics":temporal,"error_budget":error_budget,"versioning":compile_behavior,"no_silent_weakening":compile_behavior}
