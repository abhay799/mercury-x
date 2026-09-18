
from threading import Lock
from mercury.live_migration.contracts import MigrationLedgerEvent, MigrationLifecycle

class MigrationLedger:
    def __init__(self):
        self._lock = Lock()
        self._events: list[MigrationLedgerEvent] = []
        self._event_ids: set[str] = set()

    def append(self, event: MigrationLedgerEvent) -> None:
        with self._lock:
            if event.event_id in self._event_ids:
                raise ValueError("duplicate migration event")
            self._event_ids.add(event.event_id)
            self._events.append(event)

    def history(self, migration_request_id: str) -> tuple[MigrationLedgerEvent, ...]:
        return tuple(x for x in self._events if x.migration_request_id == migration_request_id)
