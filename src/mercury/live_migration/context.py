
from mercury.live_migration.contracts import MigrationCheckpoint

def validate_context_preservation(checkpoint: MigrationCheckpoint, *, restored_context_ref: str, restored_kv_ref: str | None) -> tuple[bool, str]:
    snap = checkpoint.snapshot
    if restored_context_ref != snap.session_context_ref:
        return False, "CONTEXT_MISMATCH"
    if restored_kv_ref != snap.kv_cache_ref:
        return False, "KV_CACHE_MISMATCH"
    return True, "CONTEXT_PRESERVED"
