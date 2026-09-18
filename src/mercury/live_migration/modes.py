
from mercury.live_migration.contracts import MigrationMode

def mode_requirements(mode: MigrationMode) -> tuple[str, ...]:
    if mode is MigrationMode.COLD:
        return ("CHECKPOINT", "STOP_SOURCE", "RESTORE_DESTINATION", "VERIFY")
    if mode is MigrationMode.WARM:
        return ("PRESTAGE", "CHECKPOINT_DELTA", "RESTORE_DESTINATION", "VERIFY", "CUTOVER")
    return ("PRECOPY", "QUIESCE", "FINAL_DELTA", "VERIFY", "ATOMIC_CUTOVER")
