
from mercury.live_migration.contracts import MigrationLifecycle

_ALLOWED = {
    MigrationLifecycle.REQUESTED: {MigrationLifecycle.QUALIFYING, MigrationLifecycle.ABORTED, MigrationLifecycle.STALE},
    MigrationLifecycle.QUALIFYING: {MigrationLifecycle.CHECKPOINTING, MigrationLifecycle.ABORTED, MigrationLifecycle.STALE, MigrationLifecycle.UNKNOWN},
    MigrationLifecycle.CHECKPOINTING: {MigrationLifecycle.TRANSFERRING, MigrationLifecycle.ROLLED_BACK, MigrationLifecycle.FAILED, MigrationLifecycle.STALE},
    MigrationLifecycle.TRANSFERRING: {MigrationLifecycle.RESTORING, MigrationLifecycle.ROLLED_BACK, MigrationLifecycle.FAILED, MigrationLifecycle.STALE},
    MigrationLifecycle.RESTORING: {MigrationLifecycle.VERIFYING, MigrationLifecycle.ROLLED_BACK, MigrationLifecycle.FAILED, MigrationLifecycle.STALE},
    MigrationLifecycle.VERIFYING: {MigrationLifecycle.CUTOVER_READY, MigrationLifecycle.ROLLED_BACK, MigrationLifecycle.FAILED, MigrationLifecycle.STALE},
    MigrationLifecycle.CUTOVER_READY: {MigrationLifecycle.COMMITTED, MigrationLifecycle.ROLLED_BACK, MigrationLifecycle.STALE},
}

def transition(current: MigrationLifecycle, target: MigrationLifecycle) -> MigrationLifecycle:
    if target not in _ALLOWED.get(current, set()):
        raise ValueError(f"illegal migration transition: {current.value}->{target.value}")
    return target
