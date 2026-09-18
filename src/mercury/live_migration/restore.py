
from mercury.live_migration.contracts import MigrationCheckpoint, MigrationPlan, RestoreReceipt, TransferReceipt

def restore_destination(plan: MigrationPlan, checkpoint: MigrationCheckpoint, transfer: TransferReceipt, *, restored_execution_generation: int) -> RestoreReceipt:
    if not transfer.complete:
        raise ValueError("cannot restore incomplete transfer")
    if transfer.checkpoint_id != checkpoint.checkpoint_id:
        raise ValueError("transfer/checkpoint mismatch")
    return RestoreReceipt(
        restore_id=f"restore:{plan.migration_plan_id}",
        migration_plan_id=plan.migration_plan_id,
        destination_node_id=plan.destination_node_id,
        checkpoint_id=checkpoint.checkpoint_id,
        restored_execution_generation=restored_execution_generation,
        restored_digest=transfer.transferred_digest,
        ready_for_verification=True,
    )
