from mercury.intelligence_slo.compiler import compile_sla
def revise_slo(old,sla,metric_registry):
    candidate,_=compile_sla(sla,metric_registry,version=old.version,previous_version_id=old.previous_version_id)
    if candidate.requirements==old.requirements and candidate.workload_class==old.workload_class and candidate.metric_registry_fingerprint==old.metric_registry_fingerprint:
        return old,("UNCHANGED_SLO",)
    return compile_sla(sla,metric_registry,version=old.version+1,previous_version_id=old.intelligence_slo_id)
