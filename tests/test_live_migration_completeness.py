
import pytest
from mercury.live_migration.contracts import *
from mercury.live_migration.context import validate_context_preservation
from mercury.live_migration.speculation import validate_speculation_state
from mercury.live_migration.reasoning import validate_reasoning_state
from mercury.live_migration.scheduler_slo import validate_scheduler_slo
from mercury.live_migration.security import validate_security_state
from mercury.live_migration.agreement import validate_agreement
from mercury.live_migration.failures import classify_failure
from mercury.live_migration.modes import mode_requirements
from mercury.live_migration.ledger import MigrationLedger
from mercury.live_migration.rollback import build_rollback

def request():
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

def test_modes_are_distinct():
    assert "STOP_SOURCE" in mode_requirements(MigrationMode.COLD)
    assert "PRESTAGE" in mode_requirements(MigrationMode.WARM)
    assert "ATOMIC_CUTOVER" in mode_requirements(MigrationMode.LIVE)

def test_security_rejects_authority_expansion():
    ok, _ = validate_security_state(source_authorization_context_id="a", destination_authorization_context_id="a",
        source_authorization_generation=1, destination_authorization_generation=1, destination_expands_authority=False)
    bad, reason = validate_security_state(source_authorization_context_id="a", destination_authorization_context_id="a",
        source_authorization_generation=1, destination_authorization_generation=1, destination_expands_authority=True)
    assert ok and not bad and reason == "AUTHORITY_EXPANSION_FORBIDDEN"

def test_speculation_and_reasoning_guards():
    assert validate_speculation_state(active_branches=2, migratable_branches=2, committed_branch_exists=False)[0]
    assert not validate_speculation_state(active_branches=2, migratable_branches=1, committed_branch_exists=False)[0]
    assert validate_reasoning_state(budget_id="rb", expected_budget_id="rb", consumed_units=5, max_units=10)[0]
    assert not validate_reasoning_state(budget_id="wrong", expected_budget_id="rb", consumed_units=5, max_units=10)[0]

def test_scheduler_slo_never_weakens_quality():
    assert validate_scheduler_slo(scheduler_decision_id="sd", expected_scheduler_decision_id="sd",
        slo_id="slo", expected_slo_id="slo", quality_floor=.95, required_quality_floor=.9)[0]
    assert not validate_scheduler_slo(scheduler_decision_id="sd", expected_scheduler_decision_id="sd",
        slo_id="slo", expected_slo_id="slo", quality_floor=.8, required_quality_floor=.9)[0]

def test_failure_classification_and_rollback():
    assert classify_failure(stale=True) == "STALE"
    p = MigrationPlan(migration_plan_id="p", migration_request_id="m", destination_candidate_id="c", destination_node_id="b",
        mode=MigrationMode.LIVE, source_execution_generation=1, topology_generation=1, placement_generation=1,
        scheduler_generation=1, agreement_generation=1, authorization_generation=1)
    rb = build_rollback(p, source_execution_id="e", generation=2, reason="verify failed")
    assert rb.reason == "verify failed"

def test_ledger_is_append_only_by_event_id():
    ledger = MigrationLedger()
    event = MigrationLedgerEvent(event_id="e1", migration_request_id="m1", event_type="X",
        lifecycle=MigrationLifecycle.REQUESTED, generation=1, detail="d")
    ledger.append(event)
    with pytest.raises(ValueError):
        ledger.append(event)
