from mercury.compute_negotiator.contracts import ComputeOffer
from mercury.reasoning_budget.contracts import canonical_hash

def generate_offers(*,requested_quality_floor,options,protected_constraints,resource_snapshot_generation,lease_generations=2):
    offers=[]
    for o in options:
        if o["quality_floor"] < requested_quality_floor:
            continue
        body={"q":o["quality_floor"],"latency":o["latency_ms"],"resource":o["resource_units"],
              "placements":sorted(o["placement_candidate_ids"]),"spec":o["speculation_width"],
              "snapshot":resource_snapshot_generation}
        fp=canonical_hash(body)
        offers.append(ComputeOffer(
            offer_id=canonical_hash({"offer":fp}),requested_quality_floor=requested_quality_floor,
            proposed_quality_floor=o["quality_floor"],proposed_latency_ms=o["latency_ms"],
            proposed_resource_units=o["resource_units"],placement_candidate_ids=tuple(sorted(o["placement_candidate_ids"])),
            speculation_width=o["speculation_width"],protected_constraints=tuple(sorted(protected_constraints)),
            changed_soft_constraints=tuple(sorted(o.get("changed_soft_constraints",()))),
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
