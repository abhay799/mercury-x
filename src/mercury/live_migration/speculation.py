
def validate_speculation_state(*, active_branches: int, migratable_branches: int, committed_branch_exists: bool) -> tuple[bool, str]:
    if committed_branch_exists and active_branches > 1:
        return False, "COMMITTED_BRANCH_WITH_ACTIVE_COMPETITORS"
    if migratable_branches != active_branches:
        return False, "NON_MIGRATABLE_SPECULATION_BRANCH"
    return True, "SPECULATION_STATE_MIGRATABLE"
