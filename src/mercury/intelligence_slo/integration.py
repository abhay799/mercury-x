from mercury.contracts.intelligence_requirement import GenericIntelligenceRequirementEnvelope, RequirementEnvelopeStatus, make_requirement_envelope_fingerprint
from mercury.intelligence_slo.contracts import CompilationStatus
def to_generic_requirement_view(slo):
    quality=next((r.threshold for r in slo.requirements if r.metric_id=="quality.primary"),None)
    confidence=next((r.threshold for r in slo.requirements if r.metric_id=="confidence.primary"),None)
    status={CompilationStatus.VALID:RequirementEnvelopeStatus.ACTIVE,
            CompilationStatus.AMBIGUOUS:RequirementEnvelopeStatus.AMBIGUOUS,
            CompilationStatus.UNSATISFIABLE:RequirementEnvelopeStatus.UNSATISFIABLE,
            CompilationStatus.INVALID:RequirementEnvelopeStatus.INVALID}[slo.status]
    values=dict(requirement_interface_id=slo.intelligence_slo_id,source_slo_id=slo.intelligence_slo_id,
        source_slo_version=slo.version,source_slo_fingerprint=slo.fingerprint,status=status,
        quality_floor=quality,confidence_floor=confidence,hard_requirement_ids=slo.hard_constraints,
        soft_requirement_ids=slo.soft_constraints,unknown_requirement_ids=slo.unknown_constraints,
        degradation_allowed=False,provenance_ids=slo.provenance_ids)
    return GenericIntelligenceRequirementEnvelope(fingerprint=make_requirement_envelope_fingerprint(**values),**values)
