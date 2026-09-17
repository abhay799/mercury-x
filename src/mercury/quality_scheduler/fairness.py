def fairness_adjustment(*,logical_age,fairness_weight,starvation_ceiling=20):
    if logical_age<0 or starvation_ceiling<1: raise ValueError("invalid logical age/starvation ceiling")
    starved=logical_age>=starvation_ceiling
    boost=min(.5,logical_age/max(1,starvation_ceiling)*.25)*fairness_weight
    return round(boost,6), starved, ("STARVATION_GUARD" if starved else "AGE_FAIRNESS",)
