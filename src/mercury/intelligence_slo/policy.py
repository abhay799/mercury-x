def merge_policy_layers(layers):
    merged={}
    provenance=[]
    for layer_name,requirements in layers:
        for req in requirements:
            existing=merged.get(req.metric_id)
            if existing and existing.kind.value=="HARD" and req.kind.value!="HARD":
                raise ValueError("cannot weaken inherited HARD constraint")
            merged[req.metric_id]=req
            provenance.append(f"{layer_name}:{req.requirement_id}")
    return tuple(sorted(merged.values(),key=lambda r:r.requirement_id)),tuple(provenance)
