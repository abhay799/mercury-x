def require_rollback_target(candidate):
    if not candidate.rollback_policy_id or not candidate.rollback_policy_id.strip():
        raise ValueError("rollback target required")
    return candidate.rollback_policy_id
