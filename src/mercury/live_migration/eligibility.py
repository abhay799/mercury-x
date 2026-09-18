
from mercury.live_migration.contracts import MigrationEligibility, MigrationEligibilityState, MigrationRequest

def evaluate_eligibility(
    request: MigrationRequest,
    *,
    source_healthy_enough_to_checkpoint: bool,
    checkpoint_supported: bool,
    active_non_migratable_side_effect: bool,
    state_complete: bool,
    evidence_sufficient: bool,
    current_execution_generation: int,
) -> MigrationEligibility:
    reasons = []
    if not evidence_sufficient or not state_complete:
        state = MigrationEligibilityState.UNKNOWN
        reasons.append("INSUFFICIENT_STATE_EVIDENCE")
    elif current_execution_generation != request.execution_generation:
        state = MigrationEligibilityState.INELIGIBLE
        reasons.append("STALE_EXECUTION_GENERATION")
    elif active_non_migratable_side_effect:
        state = MigrationEligibilityState.DEFER
        reasons.append("NON_MIGRATABLE_SIDE_EFFECT_ACTIVE")
    elif not checkpoint_supported or not source_healthy_enough_to_checkpoint:
        state = MigrationEligibilityState.INELIGIBLE
        reasons.append("CHECKPOINT_UNAVAILABLE")
    else:
        state = MigrationEligibilityState.ELIGIBLE
        reasons.append("ELIGIBLE")
    return MigrationEligibility(
        migration_request_id=request.migration_request_id,
        state=state,
        reasons=tuple(reasons),
        evaluated_generation=current_execution_generation,
    )
