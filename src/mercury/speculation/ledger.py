from threading import Lock

from mercury.speculation.commit import commit_verified_winner


class LogicalCommitLedger:
    """Thread-safe control-plane ledger; it performs no runtime execution."""

    def __init__(self):
        self._lock = Lock()
        self._results = {}

    def commit(self, plan, branches):
        proposed = commit_verified_winner(plan, tuple(branches))
        with self._lock:
            existing = self._results.get(plan.speculation_plan_id)
            if existing is None:
                self._results[plan.speculation_plan_id] = proposed
                return proposed
            if existing == proposed:
                return existing
            raise ValueError("speculation plan already has a different authoritative commit")

    def result_for(self, speculation_plan_id):
        with self._lock:
            return self._results.get(speculation_plan_id)
