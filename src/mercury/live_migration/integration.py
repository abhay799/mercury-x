
from mercury.live_migration.contracts import DestinationCandidate, MigrationMode, MigrationPlan, MigrationRequest

def build_plan(request: MigrationRequest, candidate: DestinationCandidate, *, mode: MigrationMode, migration_plan_id: str) -> MigrationPlan:
    if candidate.topology_generation != request.topology_generation:
        raise ValueError("stale topology candidate")
    if candidate.authorization_generation != request.authorization_generation:
        raise ValueError("stale authorization candidate")
    if not all((candidate.supports_model, candidate.supports_precision, candidate.supports_runtime, candidate.capacity_sufficient, candidate.quality_preserving)):
        raise ValueError("destination candidate is not qualified")
    return MigrationPlan(
        migration_plan_id=migration_plan_id,
        migration_request_id=request.migration_request_id,
        destination_candidate_id=candidate.candidate_id,
        destination_node_id=candidate.node_id,
        mode=mode,
        source_execution_generation=request.execution_generation,
        topology_generation=request.topology_generation,
        placement_generation=candidate.placement_generation,
        scheduler_generation=request.scheduler_generation,
        agreement_generation=request.compute_agreement_generation,
        authorization_generation=request.authorization_generation,
        checkpoint_required=True,
    )
