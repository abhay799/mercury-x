from mercury.intelligence_slo.contracts import *
from mercury.intelligence_slo.metrics import *
from mercury.intelligence_slo.compiler import compile_sla
from mercury.intelligence_slo.policy import merge_policy_layers

def registry():
    return MetricRegistry((
        MetricDefinition(metric_id="quality.primary",metric_version="v1",semantic_meaning="task quality",unit="score",evaluator_id="eval",evaluator_version="v1",threshold_direction=ThresholdDirection.MINIMUM,aggregation_rule="mean",workload_classes=("interactive",),calibration_state="UNCALIBRATED",provenance_ids=("registry",)),
        MetricDefinition(metric_id="confidence.primary",metric_version="v1",semantic_meaning="confidence",unit="score",evaluator_id="eval2",evaluator_version="v1",threshold_direction=ThresholdDirection.MINIMUM,aggregation_rule="mean",workload_classes=("interactive",),calibration_state="UNCALIBRATED",provenance_ids=("registry",)),
    ))

def test_compile_is_versioned_and_no_degradation():
    req=IntelligenceRequirement(requirement_id="q",metric_id="quality.primary",kind=ConstraintKind.HARD,threshold=.9,operator=">=",source_id="app",provenance_ids=("p",))
    sla=ApplicationSLA(sla_id="sla",workload_class="interactive",requirements=(req,),provenance_ids=("app",))
    slo,reasons=compile_sla(sla,registry())
    assert slo.status is CompilationStatus.VALID
    assert not slo.degradation_allowed
    assert slo.hard_constraints==("q",)

def test_parent_hard_constraint_cannot_be_softened():
    hard=IntelligenceRequirement(requirement_id="h",metric_id="quality.primary",kind=ConstraintKind.HARD,threshold=.9,operator=">=",source_id="org")
    soft=IntelligenceRequirement(requirement_id="s",metric_id="quality.primary",kind=ConstraintKind.SOFT,threshold=.8,operator=">=",source_id="app")
    try:
        merge_policy_layers((("org",(hard,)),("app",(soft,))))
        assert False
    except ValueError:
        assert True
