def normalize_sla(sla):
    reqs=tuple(sorted(sla.requirements,key=lambda r:r.requirement_id))
    ids=[r.requirement_id for r in reqs]
    if len(ids)!=len(set(ids)): raise ValueError("duplicate requirement id")
    return sla.model_copy(update={"requirements":reqs})
