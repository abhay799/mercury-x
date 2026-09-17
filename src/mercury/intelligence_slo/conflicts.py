from mercury.intelligence_slo.contracts import CompilationStatus
def analyze_requirements(requirements,metric_registry):
    seen={}
    for r in requirements:
        try: metric_registry.get(r.metric_id)
        except ValueError: return CompilationStatus.INVALID,("UNDEFINED_METRIC",)
        key=(r.metric_id,r.kind.value)
        if key in seen and seen[key] != (r.operator,r.threshold):
            return CompilationStatus.UNSATISFIABLE,("CONFLICTING_REQUIREMENTS",)
        seen[key]=(r.operator,r.threshold)
        if r.kind.value=="UNKNOWN":
            return CompilationStatus.AMBIGUOUS,("UNKNOWN_CONSTRAINT_KIND",)
    return CompilationStatus.VALID,("REQUIREMENTS_CONSISTENT",)
