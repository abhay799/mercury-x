
import pytest
from pydantic import ValidationError

from mercury.live_migration.contracts import *
from mercury.live_migration.eligibility import evaluate_eligibility
from mercury.live_migration.destination import qualify_destination
from mercury.live_migration.integration import build_plan
from mercury.live_migration.checkpoint import create_checkpoint
from mercury.live_migration.transfer import transfer_checkpoint
from mercury.live_migration.restore import restore_destination
from mercury.live_migration.verification import require_equivalence
from mercury.live_migration.cutover import CutoverAuthorityLedger
from mercury.live_migration.state import transition
from mercury.live_migration.staleness import validate_generations

def request(**updates):
    values = dict(
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
    values.update(updates)
    return MigrationRequest(**values)

def candidate(**updates):
    values = dict(
        candidate_id="c", node_id="b", hardware_profile_id="hb", hardware_profile_generation=13,
        topology_generation=14, placement_decision_id="pb", placement_generation=15,
        authorization_context_id="auth", authorization_generation=1,
        supports_model=True, supports_precision=True, supports_runtime=True,
        capacity_sufficient=True, quality_preserving=True, provenance_ids=("p15","t14"),
    )
    values.update(updates)
    return DestinationCandidate(**values)

def test_request_identity_and_forgery():
    r = request()
    assert len(r.fingerprint) == 64
    payload = r.model_dump()
    payload["fingerprint"] = "0"*64
    with pytest.raises(ValidationError):
        MigrationRequest.model_validate(payload)

def test_eligibility_fail_closed():
    r = request()
    good = evaluate_eligibility(r, source_healthy_enough_to_checkpoint=True, checkpoint_supported=True,
        active_non_migratable_side_effect=False, state_complete=True, evidence_sufficient=True, current_execution_generation=7)
    unknown = evaluate_eligibility(r, source_healthy_enough_to_checkpoint=True, checkpoint_supported=True,
        active_non_migratable_side_effect=False, state_complete=False, evidence_sufficient=False, current_execution_generation=7)
    assert good.state is MigrationEligibilityState.ELIGIBLE
    assert unknown.state is MigrationEligibilityState.UNKNOWN

def test_destination_quality_and_staleness():
    ok, _ = qualify_destination(request(), candidate())
    bad, reasons = qualify_destination(request(), candidate(quality_preserving=False))
    stale, stale_reasons = qualify_destination(request(), candidate(topology_generation=99))
    assert ok
    assert not bad and "QUALITY_NOT_PRESERVED" in reasons
    assert not stale and "TOPOLOGY_STALE" in stale_reasons

def test_checkpoint_transfer_restore_chain():
    r = request()
    p = build_plan(r, candidate(), mode=MigrationMode.LIVE, migration_plan_id="plan1")
    cp = create_checkpoint(r, snapshot_id="snap1", session_context_ref="ctx", kv_cache_ref="kv",
        verification_state_ref="verify", reasoning_state_ref="reason", speculation_state_ref="spec",
        scheduler_state_ref="sched", payload_digest="abc", checkpoint_generation=1)
    tr = transfer_checkpoint(p, cp, bytes_transferred=123, transferred_digest="abc")
    rr = restore_destination(p, cp, tr, restored_execution_generation=8)
    assert tr.complete and rr.ready_for_verification

def test_state_machine_rejects_illegal_jump():
    assert transition(MigrationLifecycle.REQUESTED, MigrationLifecycle.QUALIFYING) is MigrationLifecycle.QUALIFYING
    with pytest.raises(ValueError):
        transition(MigrationLifecycle.REQUESTED, MigrationLifecycle.COMMITTED)

def test_generation_staleness_detected():
    r = request()
    p = build_plan(r, candidate(), mode=MigrationMode.LIVE, migration_plan_id="plan1")
    ok, _ = validate_generations(r,p,topology_generation=14,placement_generation=15,scheduler_generation=18,agreement_generation=20,authorization_generation=1)
    bad, reasons = validate_generations(r,p,topology_generation=15,placement_generation=15,scheduler_generation=18,agreement_generation=20,authorization_generation=1)
    assert ok
    assert not bad and "TOPOLOGY_STALE" in reasons

def test_exactly_once_cutover():
    p = build_plan(request(), candidate(), mode=MigrationMode.LIVE, migration_plan_id="plan1")
    v = MigrationVerification(
        verification_id="v1", migration_plan_id="plan1", destination_node_id="b",
        model_identity_match=True, precision_match=True, graph_position_match=True,
        context_digest_match=True, reasoning_state_match=True, speculation_state_match=True,
        slo_match=True, authorization_match=True, quality_preserved=True,
    )
    ledger = CutoverAuthorityLedger()
    first = ledger.commit(plan=p, verification=v, source_execution_id="e1", destination_execution_id="e2", authority_generation=8)
    assert first.committed
    with pytest.raises(ValueError):
        ledger.commit(plan=p, verification=v, source_execution_id="e1", destination_execution_id="e2", authority_generation=9)
