def account_speculation(*, branch_count, phase16_limit, phase17_limit, per_branch_units):
    allowed=min(phase16_limit,phase17_limit)
    if branch_count>allowed: raise ValueError("speculation exceeds certified bounds")
    return round(branch_count*per_branch_units,6)
