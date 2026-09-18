from mercury.intelligence_slo.compiler import compile_sla
from mercury.intelligence_slo.contracts import (
    ApplicationSLA,
    CompilationStatus,
    ConstraintKind,
    IntelligenceRequirement,
    IntelligenceSLO,
)
from mercury.intelligence_slo.error_budget import ErrorBudget
from mercury.intelligence_slo.lifecycle import revise_slo
from mercury.intelligence_slo.metrics import MetricDefinition, MetricRegistry, ThresholdDirection
from mercury.intelligence_slo.policy import PolicyLayer, PolicyScope, merge_typed_policy_layers
from mercury.intelligence_slo.temporal import TemporalTarget


def _raises(operation):
    try:
        operation()
    except ValueError:
        return True
    return False


def _registry():
    return MetricRegistry((
        MetricDefinition(
            metric_id="quality.primary", metric_version="v1", semantic_meaning="quality", unit="score",
            evaluator_id="e", evaluator_version="v1", threshold_direction=ThresholdDirection.MINIMUM,
            aggregation_rule="mean", workload_classes=("interactive",), calibration_state="UNCALIBRATED",
            provenance_ids=("registry",),
        ),
    ))


def _requirement(requirement_id="q", *, kind=ConstraintKind.HARD, threshold=.9, metric_id="quality.primary"):
    return IntelligenceRequirement(
        requirement_id=requirement_id, metric_id=metric_id, kind=kind, threshold=threshold,
        operator=">=", source_id="app", provenance_ids=("policy",),
    )


def registry():
    metrics = _registry()
    return metrics.get("quality.primary").metric_id == "quality.primary", "metric registry executable"


def constraint_typing():
    metrics = _registry()
    mixed = ApplicationSLA(
        sla_id="typed", workload_class="interactive",
        requirements=(
            _requirement("hard", kind=ConstraintKind.HARD, threshold=.9),
            _requirement("soft", kind=ConstraintKind.SOFT, threshold=.8),
        ),
        provenance_ids=("app",),
    )
    slo, _ = compile_sla(mixed, metrics)
    typed = (
        slo.status is CompilationStatus.VALID
        and slo.hard_constraints == ("hard",)
        and slo.soft_constraints == ("soft",)
        and slo.unknown_constraints == ()
    )
    unknown = ApplicationSLA(
        sla_id="unknown", workload_class="interactive",
        requirements=(IntelligenceRequirement(
            requirement_id="u", metric_id="quality.primary", kind=ConstraintKind.UNKNOWN,
            source_id="app", provenance_ids=("policy",),
        ),),
        provenance_ids=("app",),
    )
    ambiguous, _ = compile_sla(unknown, metrics)
    missing_threshold = _raises(lambda: IntelligenceRequirement(
        requirement_id="broken", metric_id="quality.primary", kind=ConstraintKind.HARD,
        source_id="app", provenance_ids=("policy",),
    ))
    ok = typed and ambiguous.status is CompilationStatus.AMBIGUOUS and missing_threshold
    return ok, "HARD/SOFT/UNKNOWN constraint typing is preserved and UNKNOWN fails closed"


def policy_hierarchy():
    parent = PolicyLayer(
        layer_id="org", scope=PolicyScope.ORGANIZATION, requirements=(_requirement("org", threshold=.9),),
        generation=1, provenance_ids=("org-policy",),
    )
    tighter = PolicyLayer(
        layer_id="app", scope=PolicyScope.APPLICATION, requirements=(_requirement("app", threshold=.95),),
        generation=1, provenance_ids=("app-policy",),
    )
    merged, _ = merge_typed_policy_layers((tighter, parent))
    weakening = tighter.model_copy(update={"requirements": (_requirement("weak", threshold=.8),)})
    blocked = _raises(lambda: merge_typed_policy_layers((parent, weakening)))
    ok = merged[0].threshold == .95 and blocked
    return ok, "child policy cannot weaken an inherited HARD constraint"


def temporal():
    return TemporalTarget(percentile=99, window_generations=10, provenance_ids=("cert",)).percentile == 99, "temporal semantics executable"


def error_budget():
    return not ErrorBudget(
        metric_id="m", allowed_violations=1, consumed_violations=0, window_generations=10, provenance_ids=("cert",),
    ).exhausted, "error budget executable"


def versioning():
    metrics = _registry()
    sla = ApplicationSLA(
        sla_id="s", workload_class="interactive", requirements=(_requirement(),), provenance_ids=("app",),
    )
    original, _ = compile_sla(sla, metrics)
    unchanged, reasons = revise_slo(original, sla, metrics)
    changed = ApplicationSLA(
        sla_id="s", workload_class="interactive", requirements=(_requirement(threshold=.95),), provenance_ids=("rev",),
    )
    revised, _ = revise_slo(original, changed, metrics)
    ok = (
        original.version == 1 and original.previous_version_id is None
        and unchanged is original and "UNCHANGED_SLO" in reasons
        and revised.version == 2 and revised.previous_version_id == original.intelligence_slo_id
        and revised.intelligence_slo_id != original.intelligence_slo_id
    )
    return ok, "SLO revisions are immutable, lineage-bound, and versioned only on change"


def no_silent_weakening():
    metrics = _registry()
    sla_rejected = _raises(lambda: ApplicationSLA(
        sla_id="s", workload_class="interactive", requirements=(_requirement(),),
        degradation_allowed=True, provenance_ids=("app",),
    ))
    sla = ApplicationSLA(
        sla_id="s", workload_class="interactive", requirements=(_requirement(),), provenance_ids=("app",),
    )
    slo, _ = compile_sla(sla, metrics)
    compiled = slo.degradation_allowed is False
    forged = _raises(lambda: IntelligenceSLO.model_validate(slo.model_dump() | {"degradation_allowed": True}))
    return sla_rejected and compiled and forged, "compiler and contracts forbid silent quality degradation"


CHECKS = {
    "metric_registry": registry,
    "constraint_typing": constraint_typing,
    "policy_hierarchy": policy_hierarchy,
    "temporal_semantics": temporal,
    "error_budget": error_budget,
    "versioning": versioning,
    "no_silent_weakening": no_silent_weakening,
}
