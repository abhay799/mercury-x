
from mercury.live_migration.contracts import MigrationVerification

def build_verification(**kwargs) -> MigrationVerification:
    return MigrationVerification(**kwargs)

def require_equivalence(verification: MigrationVerification) -> None:
    if not verification.equivalent:
        raise ValueError("destination equivalence verification failed")
