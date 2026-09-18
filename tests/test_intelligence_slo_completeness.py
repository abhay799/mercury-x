import pytest

from mercury.contracts.intelligence_requirement import validate_active_requirement_envelope
from mercury.intelligence_slo.compiler import compile_sla
from mercury.intelligence_slo.contracts import (
    ApplicationSLA, CompilationStatus, ConstraintKind, IntelligenceRequirement, IntelligenceSLO,
)
from mercury.intelligence_slo.error_budget import ErrorBudget, build_error_budget, consume_error_budget
from mercury.intelligence_slo.integration import to_generic_requirement_view
from mercury.intelligence_slo.lifecycle import revise_slo
from mercury.intelligence_slo.metrics import MetricDefinition, MetricRegistry, ThresholdDirection
from mercury.intelligence_slo.objectives import ObjectiveNode, ObjectiveOperator, validate_objective_graph
from mercury.intelligence_slo.policy import PolicyLayer, PolicyScope, merge_typed_policy_layers
from mercury.intelligence_slo.temporal import TemporalTarget
from mercury.intelligence_slo.templates import SLOTemplate, SLOTemplateRegistry


def metric(metric_id="quality.primary"):
    return MetricDefinition(
        metric_id=metric_id, metric_version="v1", semantic_meaning="quality",
        unit="score", evaluator_id="quality-evaluator", evaluator_version="v1",
        threshold_direction=ThresholdDirection.MINIMUM, aggregation_rule="mean",
        workload_classes=("interactive",), calibration_state="UNCALIBRATED",
        provenance_ids=("registry-source",),
    )


def requirement(req_id="quality", threshold=.9, kind=ConstraintKind.HARD):
    return IntelligenceRequirement(
        requirement_id=req_id, metric_id="quality.primary", kind=kind,
        threshold=threshold, operator=">=", source_id="application",
        provenance_ids=("application-policy",),
    )


def test_metric_registry_is_content_addressed_versioned_and_order_independent():
    first = MetricRegistry((metric(), metric("confidence.primary")))
    second = MetricRegistry((metric("confidence.primary"), metric()))
    assert first.fingerprint == second.fingerprint
    assert first.generation == 1
    with pytest.raises(ValueError, match="undefined"):
        first.get("missing")


def test_policy_hierarchy_requires_override_authority_and_preserves_hard_parent():
    parent = PolicyLayer(layer_id="org", scope=PolicyScope.ORGANIZATION,
                         requirements=(requirement("org-quality", .9),),
                         generation=1, provenance_ids=("org-policy",))
    child = PolicyLayer(layer_id="app", scope=PolicyScope.APPLICATION,
                        requirements=(requirement("app-quality", .95),),
                        generation=1, provenance_ids=("app-policy",), override_authority_ids=())
    merged, provenance = merge_typed_policy_layers((child, parent))
    assert merged[0].threshold == .95 and provenance
    weakening = child.model_copy(update={"requirements": (requirement("weak", .8),)})
    with pytest.raises(ValueError, match="weaken"):
        merge_typed_policy_layers((parent, weakening))


def test_temporal_error_budget_objective_and_template_semantics_fail_closed():
    temporal = TemporalTarget(percentile=99, window_generations=10, availability_window_generations=20,
                              burst_limit=2, provenance_ids=("sla",))
    assert temporal.fingerprint
    protected = build_error_budget(metric_id="privacy.access", allowed_violations=None,
                                   window_generations=10, provenance_ids=("policy",))
    assert protected.allowed_violations == 0
    exhausted = consume_error_budget(protected, 1)
    assert exhausted.exhausted
    nodes = (
        ObjectiveNode(node_id="root", operator=ObjectiveOperator.AND, child_ids=("leaf",)),
        ObjectiveNode(node_id="leaf", operator=ObjectiveOperator.REQUIREMENT,
                      requirement_id="quality"),
    )
    assert validate_objective_graph(nodes, hard_requirement_ids=("quality",)) == ("leaf", "root")
    with pytest.raises(ValueError, match="circular"):
        validate_objective_graph((ObjectiveNode(node_id="x", operator=ObjectiveOperator.AND,
                                                child_ids=("x",)),))
    registry = SLOTemplateRegistry()
    registry.register(SLOTemplate(template_id="interactive", version=1,
                                  workload_class="interactive", requirements=(requirement(),),
                                  provenance_ids=("template-source",)))
    assert registry.expand("interactive")[1]


def test_compiler_and_lifecycle_emit_integrity_checked_generic_requirement_envelope():
    registry = MetricRegistry((metric(),))
    sla = ApplicationSLA(sla_id="sla", workload_class="interactive",
                         requirements=(requirement(),), provenance_ids=("application",))
    slo, _ = compile_sla(sla, registry)
    assert slo.status is CompilationStatus.VALID and not slo.degradation_allowed
    envelope = to_generic_requirement_view(slo)
    assert validate_active_requirement_envelope(envelope) == envelope
    assert envelope.quality_floor == .9
    forged = slo.model_dump() | {"fingerprint": "forged"}
    with pytest.raises(ValueError, match="fingerprint"):
        IntelligenceSLO.model_validate(forged)
    assert revise_slo(slo, sla, registry)[0] == slo
    changed = ApplicationSLA(sla_id="sla", workload_class="interactive",
                             requirements=(requirement(threshold=.95),), provenance_ids=("change",))
    revised, _ = revise_slo(slo, changed, registry)
    assert revised.version == 2 and revised.previous_version_id == slo.intelligence_slo_id
