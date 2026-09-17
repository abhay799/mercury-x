from mercury.intelligence_slo.compiler import compile_sla
def revise_slo(old,sla,metric_registry):
    return compile_sla(sla,metric_registry,version=old.version+1,previous_version_id=old.intelligence_slo_id)
