from mercury.intelligence_slo.normalize import normalize_sla
from mercury.intelligence_slo.conflicts import analyze_requirements
from mercury.intelligence_slo.contracts import IntelligenceSLO,ConstraintKind
from mercury.reasoning_budget.contracts import canonical_hash
def compile_sla(sla,metric_registry,*,version=1,previous_version_id=None):
    sla=normalize_sla(sla)
    status,reasons=analyze_requirements(sla.requirements,metric_registry)
    hard=tuple(sorted(r.requirement_id for r in sla.requirements if r.kind is ConstraintKind.HARD))
    soft=tuple(sorted(r.requirement_id for r in sla.requirements if r.kind is ConstraintKind.SOFT))
    unknown=tuple(sorted(r.requirement_id for r in sla.requirements if r.kind is ConstraintKind.UNKNOWN))
    prov=tuple(sorted({p for r in sla.requirements for p in r.provenance_ids} | {r.source_id for r in sla.requirements}))
    body={"sla":sla.sla_id,"version":version,"requirements":[r.model_dump(mode="json") for r in sla.requirements],
          "degradation_allowed":False,"status":status.value,"previous":previous_version_id}
    fp=canonical_hash(body); sid=canonical_hash({"intelligence_slo":fp})
    return IntelligenceSLO(intelligence_slo_id=sid,source_sla_id=sla.sla_id,version=version,
        previous_version_id=previous_version_id,requirements=sla.requirements,degradation_allowed=False,
        status=status,hard_constraints=hard,soft_constraints=soft,unknown_constraints=unknown,
        provenance_ids=prov,fingerprint=fp),reasons
