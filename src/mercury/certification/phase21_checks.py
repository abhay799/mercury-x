
from mercury.live_migration.contracts import (
    DestinationCandidate, MigrationMode, MigrationRequest, MigrationTrigger,
)
from mercury.live_migration.destination import qualify_destination
from mercury.live_migration.eligibility import evaluate_eligibility
from mercury.live_migration.integration import build_plan
from mercury.live_migration.security import validate_security_state
from mercury.live_migration.state import transition
from mercury.live_migration.contracts import MigrationLifecycle, MigrationEligibilityState

def _request():
    return MigrationRequest(
        migration_request_id="m1", workload_id="w", execution_id="e1", source_node_id="a",
        trigger=MigrationTrigger.NODE_DEGRADATION, model_id="model", model_version="v1", precision="bf16",
        execution_graph_id="g", execution_graph_position="s1",
        hardware_profile_id="h", hardware_profile_generation=13, topology_generation=14,
        placement_decision_id="p", placement_generation=15, speculation_plan_id="sp", speculation_generation=16,
        reasoning_budget_id="rb", reasoning_budget_generation=17, scheduler_decision_id="sd", scheduler_generation=18,
        intelligence_slo_id="slo", intelligence_slo_version=1, compute_agreement_id="ag", compute_agreement_generation=20,
        authorization_context_id="auth", authorization_generation=1, execution_generation=7,
        provenance_ids=("13","14","15","16","17","18","19","20"),
    )

def _candidate():
    return DestinationCandidate(
        candidate_id="c", node_id="b", hardware_profile_id="hb", hardware_profile_generation=13,
        topology_generation=14, placement_decision_id="pb", placement_generation=15,
        authorization_context_id="auth", authorization_generation=1,
        supports_model=True, supports_precision=True, supports_runtime=True,
        capacity_sufficient=True, quality_preserving=True, provenance_ids=("p15","t14"),
    )

def contracts():
    r = _request()
    return bool(r.fingerprint), "migration request fingerprinted"

def eligibility():
    r = _request()
    result = evaluate_eligibility(r, source_healthy_enough_to_checkpoint=True, checkpoint_supported=True,
                                  active_non_migratable_side_effect=False, state_complete=True,
                                  evidence_sufficient=True, current_execution_generation=7)
    return result.state is MigrationEligibilityState.ELIGIBLE, "eligibility executable"

def destination():
    ok, _ = qualify_destination(_request(), _candidate())
    return ok, "destination qualification executable"

def lifecycle():
    return transition(MigrationLifecycle.REQUESTED, MigrationLifecycle.QUALIFYING) is MigrationLifecycle.QUALIFYING, "state machine executable"

def no_quality_degrade():
    c = _candidate().model_copy(update={"quality_preserving": False})
    ok, reasons = qualify_destination(_request(), c)
    return (not ok) and "QUALITY_NOT_PRESERVED" in reasons, "destination cannot weaken quality"

def security():
    ok, _ = validate_security_state(
        source_authorization_context_id="auth", destination_authorization_context_id="auth",
        source_authorization_generation=1, destination_authorization_generation=1,
        destination_expands_authority=False,
    )
    bad, _ = validate_security_state(
        source_authorization_context_id="auth", destination_authorization_context_id="auth",
        source_authorization_generation=1, destination_authorization_generation=1,
        destination_expands_authority=True,
    )
    return ok and not bad, "authority cannot expand during migration"

def planning():
    plan = build_plan(_request(), _candidate(), mode=MigrationMode.LIVE, migration_plan_id="plan")
    return plan.destination_node_id == "b", "typed migration plan executable"

CHECKS = {
    "contracts": contracts,
    "eligibility": eligibility,
    "destination": destination,
    "lifecycle": lifecycle,
    "no_quality_degrade": no_quality_degrade,
    "security": security,
    "planning": planning,
}
