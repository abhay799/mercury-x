from mercury.hardware_personality.affinity import derive_workload_affinities
from mercury.hardware_personality.capabilities import build_capability_matrix, resolve_capability
from mercury.hardware_personality.compatibility import evaluate_hardware_compatibility
from mercury.hardware_personality.compatibility import requirement_from_phase12_segment
from mercury.hardware_personality.contracts import (
    CapabilitySupportState, HardwareAffinityLevel, HardwareClass,
    HardwareCompatibilityState, HardwareEvidenceClass, HardwarePrecision,
    HardwareRequirement, HardwareTrustState,
    HardwareMeasurementContext,
    make_measurement_context_id,
)
from mercury.hardware_personality.lifecycle import (
    build_hardware_personality_profile, evaluate_profile_staleness,
    refresh_hardware_profile, transition_hardware_trust,
)
from mercury.hardware_personality.normalization import normalize_hardware_descriptor
from mercury.hardware_personality.probes import LocalCPUProbeBackend


def _descriptor():
    return normalize_hardware_descriptor({
        "hardware_class": "CPU",
        "vendor": "Generic",
        "architecture": "x86_64",
        "device_family": "CPU",
        "device_model": "cert-fixture",
        "memory_capacity_bytes": 16 * 1024**3,
    })


def _evidence(desc, property_name, value, *, cls=HardwareEvidenceClass.PROBED, sequence=1, benchmark_id=None):
    from mercury.hardware_personality.contracts import HardwareEvidenceRecord, make_evidence_id
    eid, fp = make_evidence_id(
        hardware_id=desc.hardware_id, evidence_class=cls,
        property_name=property_name, source_id="cert",
        sequence=sequence, generation=1,
        declared_value=value if cls is HardwareEvidenceClass.DECLARED else None,
        observed_value=value if cls is not HardwareEvidenceClass.DECLARED else None,
    )
    return HardwareEvidenceRecord(
        evidence_id=eid, hardware_id=desc.hardware_id, evidence_class=cls,
        property_name=property_name,
        declared_value=value if cls is HardwareEvidenceClass.DECLARED else None,
        observed_value=value if cls is not HardwareEvidenceClass.DECLARED else None,
        source_id="cert", probe_id="cert-probe" if cls is HardwareEvidenceClass.PROBED else None,
        benchmark_id=benchmark_id, sequence=sequence, generation=1,
        verification_status=True, evidence_fingerprint=fp,
    )


def exact_enums():
    ok = (
        {x.value for x in HardwareClass} == {"CPU","GPU","TPU","NPU","OTHER_ACCELERATOR"}
        and {x.value for x in HardwareEvidenceClass} == {"DECLARED","PROBED","MEASURED","DERIVED"}
        and {x.value for x in HardwareTrustState} == {"UNVERIFIED","VERIFIED","STALE","INVALID"}
        and {x.value for x in CapabilitySupportState} == {"CAPABLE","INCAPABLE","UNKNOWN"}
        and {x.value for x in HardwarePrecision} == {"FP32","TF32","FP16","BF16","FP8","INT8","INT4"}
    )
    return ok, "exact enum sets validated"


def deterministic_identity():
    a = _descriptor()
    b = _descriptor()
    return a.hardware_id == b.hardware_id, "hardware identity deterministic"


def evidence_identity():
    d = _descriptor()
    a = _evidence(d, "precision.FP32", "supported")
    b = _evidence(d, "precision.FP32", "supported")
    return a.evidence_id == b.evidence_id, "evidence identity deterministic"


def conflict_preserved():
    d = _descriptor()
    ev = (_evidence(d,"precision.BF16","supported",sequence=1),
          _evidence(d,"precision.BF16","unsupported",sequence=2))
    r = resolve_capability("precision.BF16", ev)
    return r.support_state is CapabilitySupportState.UNKNOWN and r.conflict, "conflict preserved as UNKNOWN"


def unknown_without_evidence():
    return resolve_capability("precision.FP8", ()).support_state is CapabilitySupportState.UNKNOWN, "missing evidence is UNKNOWN"


def cpu_probe():
    d = _descriptor()
    out = LocalCPUProbeBackend().probe(d)
    return bool(out) and all(x.hardware_id == d.hardware_id for x in out), "CPU probe executable"


def affinity_evidence():
    d = _descriptor()
    aff = derive_workload_affinities(d, build_capability_matrix(()), ())
    return all(x.level is HardwareAffinityLevel.UNKNOWN for x in aff), "affinity requires evidence"


def compatibility_behavior():
    d = _descriptor()
    ev = (_evidence(d,"precision.FP32","supported"),)
    p = build_hardware_personality_profile(
        descriptor=d,
        evidence=ev,
        trust_state=HardwareTrustState.VERIFIED,
    )
    r = evaluate_hardware_compatibility(p, HardwareRequirement(
        requirement_id="r", required_precision=HardwarePrecision.FP32
    ))
    return r.state is HardwareCompatibilityState.COMPATIBLE, "explicit compatibility works"


def lifecycle_behavior():
    d = _descriptor()
    p = build_hardware_personality_profile(
        descriptor=d,
        evidence=(_evidence(d, "precision.FP32", "supported"),),
    )
    v = transition_hardware_trust(p, HardwareTrustState.VERIFIED)
    s = transition_hardware_trust(v, HardwareTrustState.STALE)
    refreshed = refresh_hardware_profile(s, evidence=())
    ok = refreshed.profile_generation == p.profile_generation + 1 and evaluate_profile_staleness(
        p, current_generation=3, max_generation_age=1
    )
    return bool(ok), "lifecycle/generation/staleness executable"


def measured_lineage():
    d = _descriptor()
    try:
        build_hardware_personality_profile(
            descriptor=d, evidence=(), measured_memory_bandwidth_bytes_per_s=80
        )
        return False, "measured field incorrectly accepted without evidence"
    except ValueError:
        return True, "measured value requires evidence lineage"


def boundary_no_side_effects():
    descriptor = _descriptor()
    rejected = True
    for forbidden in ("model_id", "placement", "scheduler", "runtime_process", "migration"):
        try:
            type(descriptor).model_validate(descriptor.model_dump() | {forbidden: "forbidden"})
            rejected = False
        except ValueError:
            pass
    return rejected, "contracts behaviorally reject Phase 14+ decision and execution fields"


def measurement_context_behavior():
    descriptor = _descriptor()
    values = dict(
        benchmark_id="cert-benchmark", benchmark_version="v1",
        runtime_applicable=True, runtime_id="cert-runtime", runtime_version="v1",
        driver_applicable=False, software_stack_applicable=True,
        software_stack_id="cert-stack", software_stack_version="v1",
        precision_applicable=True, precision_mode=HardwarePrecision.FP32,
        environment_applicable=False, hardware_profile_generation=1,
        evidence_generation=1, provenance_ids=("cert",),
    )
    first = HardwareMeasurementContext(context_id=make_measurement_context_id(**values), **values)
    changed = values | {"runtime_version": "v2"}
    second = HardwareMeasurementContext(context_id=make_measurement_context_id(**changed), **changed)
    missing_rejected = False
    try:
        _evidence(descriptor, "memory.bandwidth_bytes_per_s", "80", cls=HardwareEvidenceClass.MEASURED, benchmark_id="cert-benchmark")
    except ValueError:
        missing_rejected = True
    return first.context_id != second.context_id and missing_rejected, "typed measurement context changes semantic identity and is mandatory for measured evidence"


def phase12_requirement_behavior():
    from tests._phase12_helpers import make_segment
    segment = make_segment()
    requirement = requirement_from_phase12_segment(segment)
    return requirement.requirement_id == f"phase12:{segment.segment_id}", "Phase 12 identity is preserved without inferred hardware semantics"


CHECKS = {
    "certified_vocabularies": exact_enums,
    "hardware_identity": deterministic_identity,
    "evidence_identity": evidence_identity,
    "measurement_context": measurement_context_behavior,
    "conflict_preservation": conflict_preserved,
    "unknown_without_evidence": unknown_without_evidence,
    "cpu_probe": cpu_probe,
    "affinity_evidence": affinity_evidence,
    "compatibility": compatibility_behavior,
    "profile_lifecycle": lifecycle_behavior,
    "measured_lineage": measured_lineage,
    "phase12_requirement": phase12_requirement_behavior,
    "phase_boundary": boundary_no_side_effects,
}
