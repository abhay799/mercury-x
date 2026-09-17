def propagate_constraints(*constraint_sets):
    merged={}
    for constraints in constraint_sets:
        for key,value in constraints.items():
            if key in merged and merged[key]!=value:
                raise ValueError(f"constraint contradiction: {key}")
            merged[key]=value
    return dict(sorted(merged.items()))
