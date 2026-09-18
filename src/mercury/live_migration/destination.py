
from mercury.live_migration.contracts import DestinationCandidate, MigrationRequest

def qualify_destination(request: MigrationRequest, candidate: DestinationCandidate) -> tuple[bool, tuple[str, ...]]:
    reasons = []
    checks = {
        "MODEL_UNSUPPORTED": candidate.supports_model,
        "PRECISION_UNSUPPORTED": candidate.supports_precision,
        "RUNTIME_UNSUPPORTED": candidate.supports_runtime,
        "CAPACITY_INSUFFICIENT": candidate.capacity_sufficient,
        "QUALITY_NOT_PRESERVED": candidate.quality_preserving,
        "TOPOLOGY_STALE": candidate.topology_generation == request.topology_generation,
        "AUTHORIZATION_STALE": candidate.authorization_generation == request.authorization_generation,
    }
    for reason, ok in checks.items():
        if not ok:
            reasons.append(reason)
    return not reasons, tuple(reasons or ("QUALIFIED",))
