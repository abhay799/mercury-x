def score_features(f):
    raw=.45*f.compatibility_score+.30*f.locality_score+.25*f.evidence_score-.35*f.uncertainty_penalty
    return max(0.0,min(1.0,round(raw,6)))
