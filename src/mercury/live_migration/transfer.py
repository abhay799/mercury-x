
from mercury.live_migration.contracts import MigrationCheckpoint, MigrationPlan, TransferReceipt

def transfer_checkpoint(plan: MigrationPlan, checkpoint: MigrationCheckpoint, *, bytes_transferred: int, transferred_digest: str) -> TransferReceipt:
    if checkpoint.migration_request_id != plan.migration_request_id:
        raise ValueError("checkpoint/plan request mismatch")
    complete = transferred_digest == checkpoint.snapshot.payload_digest
    return TransferReceipt(
        transfer_id=f"transfer:{plan.migration_plan_id}",
        migration_plan_id=plan.migration_plan_id,
        checkpoint_id=checkpoint.checkpoint_id,
        destination_node_id=plan.destination_node_id,
        transferred_digest=transferred_digest,
        bytes_transferred=bytes_transferred,
        complete=complete,
    )
