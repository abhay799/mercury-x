
from mercury.live_migration.contracts import MigrationTrigger

def validate_trigger(trigger: MigrationTrigger, *, evidence_present: bool) -> tuple[bool, str]:
    if not evidence_present:
        return False, "TRIGGER_EVIDENCE_MISSING"
    return True, trigger.value
