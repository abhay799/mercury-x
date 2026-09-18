from mercury.compute_negotiator.contracts import ComputeOffer
from mercury.reasoning_budget.contracts import canonical_hash

def generate_offers(*,requested_quality_floor,options,protected_constraints,resource_snapshot_generation,lease_generations=2,request_id="legacy-request"):
    offers=[]
    for o in options:
        if o["quality_floor"] < requested_quality_floor:
            continue
        protected=tuple(sorted(set(protected_constraints)|{"quality","verification","safety","privacy","authorization","residency"}))
        changes=tuple(sorted(o.get("changed_soft_constraints",())))
        body={"request_id":request_id,"q":float(o["quality_floor"]),"requested_q":float(requested_quality_floor),"latency":o["latency_ms"],"resource":float(o["resource_units"]),
              "placements":sorted(o["placement_candidate_ids"]),"spec":o["speculation_width"],
              "protected":list(protected),"changes":list(changes),"snapshot":resource_snapshot_generation,
              "lease":resource_snapshot_generation+lease_generations}
        fp=canonical_hash(body)
        offers.append(ComputeOffer(
            offer_id=canonical_hash({"offer":fp}),request_id=request_id,requested_quality_floor=requested_quality_floor,
            proposed_quality_floor=o["quality_floor"],proposed_latency_ms=o["latency_ms"],
            proposed_resource_units=o["resource_units"],placement_candidate_ids=tuple(sorted(o["placement_candidate_ids"])),
            speculation_width=o["speculation_width"],protected_constraints=protected,
            changed_soft_constraints=changes,
            resource_snapshot_generation=resource_snapshot_generation,
            lease_until_generation=resource_snapshot_generation+lease_generations,
            reason_codes=("PARETO_FEASIBLE_OFFER",),fingerprint=fp))
    # remove dominated offers while quality is protected
    out=[]
    for a in sorted(offers,key=lambda x:x.offer_id):
        dominated=False
        for b in offers:
            if b.offer_id==a.offer_id: continue
            if (b.proposed_quality_floor>=a.proposed_quality_floor and
                b.proposed_latency_ms<=a.proposed_latency_ms and
                b.proposed_resource_units<=a.proposed_resource_units and
                (b.proposed_quality_floor>a.proposed_quality_floor or b.proposed_latency_ms<a.proposed_latency_ms or b.proposed_resource_units<a.proposed_resource_units)):
                dominated=True; break
        if not dominated: out.append(a)
    return tuple(out)
