
from mercury.live_migration.contracts import MigrationPlan, RollbackRecord

def build_rollback(plan: MigrationPlan, *, source_execution_id: str, generation: int, reason: str) -> RollbackRecord:
    if not reason.strip():
        raise ValueError("rollback reason required")
    return RollbackRecord(
        rollback_id=f"rollback:{plan.migration_request_id}:{generation}",
        migration_plan_id=plan.migration_plan_id,
        restored_source_execution_id=source_execution_id,
        rollback_generation=generation,
        reason=reason,
    )
