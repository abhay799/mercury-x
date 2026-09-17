from mercury.hardware_personality.contracts import (
    HardwareClass,
    HardwareDescriptor,
    HardwareEvidenceClass,
    HardwareEvidenceRecord,
    HardwareTrustState,
    VirtualizationState,
    make_evidence_id,
    make_hardware_id,
    HardwareMeasurementContext,
    HardwarePrecision,
    make_measurement_context_id,
)
from mercury.hardware_personality.lifecycle import build_hardware_personality_profile


def descriptor(hardware_class=HardwareClass.CPU, memory=16 * 1024**3):
    vendor = "Generic"
    architecture = "x86_64" if hardware_class is HardwareClass.CPU else "accelerator"
    family = hardware_class.value
    model = f"{hardware_class.value}-fixture"
    hardware_id = make_hardware_id(
        hardware_class=hardware_class,
        vendor=vendor,
        architecture=architecture,
        device_family=family,
        device_model=model,
    )
    return HardwareDescriptor(
        hardware_id=hardware_id,
        hardware_class=hardware_class,
        vendor=vendor,
        architecture=architecture,
        device_family=family,
        device_model=model,
        memory_capacity_bytes=memory,
        virtualization_state=VirtualizationState.UNKNOWN,
    )


def evidence(desc, property_name, value, *, cls=HardwareEvidenceClass.PROBED, sequence=1, verified=True, benchmark_id=None):
    measurement_context = None
    if cls is HardwareEvidenceClass.MEASURED:
        context_values = dict(
            benchmark_id=benchmark_id or "fixture-benchmark", benchmark_version="v1",
            runtime_applicable=True, runtime_id="fixture-runtime", runtime_version="v1",
            driver_applicable=False, software_stack_applicable=True,
            software_stack_id="fixture-stack", software_stack_version="v1",
            precision_applicable=True, precision_mode=HardwarePrecision.FP32,
            environment_applicable=False, hardware_profile_generation=1,
            evidence_generation=1, provenance_ids=("fixture",),
        )
        measurement_context = HardwareMeasurementContext(
            context_id=make_measurement_context_id(**context_values), **context_values
        )
    evidence_id, fp = make_evidence_id(
        hardware_id=desc.hardware_id,
        evidence_class=cls,
        property_name=property_name,
        source_id="fixture",
        sequence=sequence,
        generation=1,
        declared_value=value if cls is HardwareEvidenceClass.DECLARED else None,
        observed_value=value if cls is not HardwareEvidenceClass.DECLARED else None,
        measurement_context=measurement_context,
    )
    return HardwareEvidenceRecord(
        evidence_id=evidence_id,
        hardware_id=desc.hardware_id,
        evidence_class=cls,
        property_name=property_name,
        declared_value=value if cls is HardwareEvidenceClass.DECLARED else None,
        observed_value=value if cls is not HardwareEvidenceClass.DECLARED else None,
        source_id="fixture",
        probe_id="fixture-probe" if cls is HardwareEvidenceClass.PROBED else None,
        benchmark_id=(benchmark_id or "fixture-benchmark") if cls is HardwareEvidenceClass.MEASURED else None,
        sequence=sequence,
        generation=1,
        verification_status=verified,
        evidence_fingerprint=fp,
        measurement_context=measurement_context,
    )


def profile(hardware_class=HardwareClass.CPU):
    desc = descriptor(hardware_class=hardware_class)
    ev = (
        evidence(desc, "precision.FP32", "supported", sequence=1),
        evidence(desc, "runtime.remote_execution", "supported", sequence=2),
    )
    return build_hardware_personality_profile(
        descriptor=desc,
        evidence=ev,
        trust_state=HardwareTrustState.VERIFIED,
    )
