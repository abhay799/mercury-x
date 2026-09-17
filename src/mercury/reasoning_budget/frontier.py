def dominates(a,b):
    aq=a.expected_quality_low
    bq=b.expected_quality_low
    if aq is None or bq is None:
        return False
    no_worse = (
        aq >= bq and
        (a.expected_latency_ms or 10**18) <= (b.expected_latency_ms or 10**18) and
        a.compute_units <= b.compute_units and
        a.verification_depth >= b.verification_depth and
        a.uncertainty <= b.uncertainty
    )
    strictly = (
        aq > bq or
        (a.expected_latency_ms or 10**18) < (b.expected_latency_ms or 10**18) or
        a.compute_units < b.compute_units or
        a.verification_depth > b.verification_depth or
        a.uncertainty < b.uncertainty
    )
    return no_worse and strictly

def build_budget_frontier(candidates):
    ordered=tuple(sorted(candidates,key=lambda x:x.candidate_id))
    out=[]
    for c in ordered:
        if not any(dominates(other,c) for other in ordered if other.candidate_id!=c.candidate_id):
            out.append(c)
    return tuple(out)
