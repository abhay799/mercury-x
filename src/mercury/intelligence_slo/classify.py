from mercury.intelligence_slo.contracts import ConstraintKind
PROTECTED_PREFIXES=("safety.","privacy.","authorization.","residency.","verification.")
def classify_requirement(req):
    if req.kind is not ConstraintKind.UNKNOWN:
        return req.kind
    if req.metric_id.startswith(PROTECTED_PREFIXES):
        return ConstraintKind.HARD
    return ConstraintKind.UNKNOWN
