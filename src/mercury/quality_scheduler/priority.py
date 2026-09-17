from mercury.quality_scheduler.contracts import PriorityClass
def priority_score(f):
    score=(.22*f.deadline_pressure+.22*f.quality_risk+.10*f.verification_pressure+.10*f.uncertainty+
           .08*f.budget_pressure+.08*(1-f.placement_confidence)+.08*f.resource_pressure+
           .06*(1-f.locality_score)+.06*f.fragmentation_cost)
    age_boost=min(.20,f.logical_age*.01)*min(2.0,f.fairness_weight)
    return round(min(1.0,score+age_boost),6)
def classify_priority(score):
    return PriorityClass.CRITICAL if score>=.8 else PriorityClass.HIGH if score>=.6 else PriorityClass.NORMAL if score>=.3 else PriorityClass.LOW
