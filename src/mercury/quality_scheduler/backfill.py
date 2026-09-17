def select_backfill(candidates, *, protected_slack_units):
    eligible=[c for c in candidates if c["duration_units"] is not None and c["duration_units"]<=protected_slack_units and c["hard_requirements_satisfied"]]
    return tuple(sorted((c["workload_id"] for c in eligible)))
