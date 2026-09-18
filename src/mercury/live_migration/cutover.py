
from threading import Lock
from mercury.live_migration.contracts import CutoverRecord, MigrationPlan, MigrationVerification

class CutoverAuthorityLedger:
    def __init__(self):
        self._lock = Lock()
        self._committed: dict[str, CutoverRecord] = {}

    def commit(
        self, *, plan: MigrationPlan, verification: MigrationVerification,
        source_execution_id: str, destination_execution_id: str, authority_generation: int
    ) -> CutoverRecord:
        if not verification.equivalent:
            raise ValueError("cannot cut over before equivalence verification")
        with self._lock:
            if plan.migration_request_id in self._committed:
                raise ValueError("migration request already committed")
            record = CutoverRecord(
                cutover_id=f"cutover:{plan.migration_request_id}:{authority_generation}",
                migration_plan_id=plan.migration_plan_id,
                source_execution_id=source_execution_id,
                destination_execution_id=destination_execution_id,
                authority_generation=authority_generation,
                committed=True,
            )
            self._committed[plan.migration_request_id] = record
            return record
