
from mercury.live_migration.contracts import (
    MigrationLedgerEvent, MigrationLifecycle, MigrationMode, MigrationRequest, DestinationCandidate
)
from mercury.live_migration.destination import qualify_destination
from mercury.live_migration.integration import build_plan
from mercury.live_migration.ledger import MigrationLedger

class MigrationEngine:
    """Control-plane orchestrator only. It does not execute runtime migration itself."""

    def __init__(self, ledger: MigrationLedger | None = None):
        self.ledger = ledger or MigrationLedger()

    def qualify_and_plan(self, request: MigrationRequest, candidate: DestinationCandidate, *, mode: MigrationMode, migration_plan_id: str):
        ok, reasons = qualify_destination(request, candidate)
        if not ok:
            raise ValueError("destination rejected: " + ",".join(reasons))
        plan = build_plan(request, candidate, mode=mode, migration_plan_id=migration_plan_id)
        self.ledger.append(MigrationLedgerEvent(
            event_id=f"event:{migration_plan_id}:planned",
            migration_request_id=request.migration_request_id,
            event_type="PLAN_CREATED",
            lifecycle=MigrationLifecycle.QUALIFYING,
            generation=request.execution_generation,
            detail=candidate.node_id,
        ))
        return plan
