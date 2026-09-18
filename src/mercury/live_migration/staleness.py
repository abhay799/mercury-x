
from mercury.live_migration.contracts import MigrationPlan, MigrationRequest

def validate_generations(
    request: MigrationRequest,
    plan: MigrationPlan,
    *,
    topology_generation: int,
    placement_generation: int,
    scheduler_generation: int,
    agreement_generation: int,
    authorization_generation: int,
) -> tuple[bool, tuple[str, ...]]:
    reasons = []
    expected = (
        ("TOPOLOGY_STALE", request.topology_generation, topology_generation),
        ("PLACEMENT_STALE", plan.placement_generation, placement_generation),
        ("SCHEDULER_STALE", plan.scheduler_generation, scheduler_generation),
        ("AGREEMENT_STALE", plan.agreement_generation, agreement_generation),
        ("AUTHORIZATION_STALE", plan.authorization_generation, authorization_generation),
    )
    for reason, wanted, current in expected:
        if wanted != current:
            reasons.append(reason)
    return not reasons, tuple(reasons or ("CURRENT",))
