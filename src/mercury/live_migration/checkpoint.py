
from mercury.live_migration.contracts import MigrationCheckpoint, MigrationRequest, MigrationStateSnapshot

def create_checkpoint(
    request: MigrationRequest,
    *,
    snapshot_id: str,
    session_context_ref: str,
    kv_cache_ref: str | None,
    verification_state_ref: str | None,
    reasoning_state_ref: str,
    speculation_state_ref: str,
    scheduler_state_ref: str,
    payload_digest: str,
    checkpoint_generation: int,
) -> MigrationCheckpoint:
    snapshot = MigrationStateSnapshot(
        snapshot_id=snapshot_id,
        migration_request_id=request.migration_request_id,
        execution_generation=request.execution_generation,
        model_id=request.model_id,
        model_version=request.model_version,
        precision=request.precision,
        execution_graph_position=request.execution_graph_position,
        session_context_ref=session_context_ref,
        kv_cache_ref=kv_cache_ref,
        verification_state_ref=verification_state_ref,
        reasoning_state_ref=reasoning_state_ref,
        speculation_state_ref=speculation_state_ref,
        scheduler_state_ref=scheduler_state_ref,
        slo_ref=request.intelligence_slo_id,
        agreement_ref=request.compute_agreement_id,
        authorization_context_id=request.authorization_context_id,
        authorization_generation=request.authorization_generation,
        payload_digest=payload_digest,
    )
    return MigrationCheckpoint(
        checkpoint_id=f"checkpoint:{request.migration_request_id}:{checkpoint_generation}",
        migration_request_id=request.migration_request_id,
        snapshot=snapshot,
        source_execution_generation=request.execution_generation,
        checkpoint_generation=checkpoint_generation,
        sealed=True,
    )
