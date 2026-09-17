from mercury.hardware_personality.contracts import (
    CapabilityAssessment,
    CapabilitySupportState,
    HardwareAffinityDimension,
    HardwareAffinityLevel,
    HardwareDescriptor,
    HardwareEvidenceRecord,
    HardwareWorkloadAffinity,
)


def derive_workload_affinities(
    descriptor: HardwareDescriptor,
    capabilities: tuple[CapabilityAssessment, ...],
    evidence: tuple[HardwareEvidenceRecord, ...],
) -> tuple[HardwareWorkloadAffinity, ...]:
    verified_evidence = tuple(sorted(
        (item for item in evidence if item.verification_status),
        key=lambda item: item.evidence_id,
    ))
    evidence_ids = tuple(item.evidence_id for item in verified_evidence)
    caps = {item.property_name: item for item in capabilities}

    def state(name: str):
        item = caps.get(name)
        return None if item is None else item.support_state

    def any_capable(names):
        return any(state(name) is CapabilitySupportState.CAPABLE for name in names)

    fast_precision = any_capable(
        ("precision.FP16", "precision.BF16", "precision.FP8", "precision.INT8")
    )
    p2p = state("interconnect.peer_to_peer") is CapabilitySupportState.CAPABLE
    remote = state("runtime.remote_execution") is CapabilitySupportState.CAPABLE
    memory_known = descriptor.memory_capacity_bytes is not None and any(
        item.property_name in {"memory.capacity_bytes", "descriptor.memory_capacity_bytes"}
        for item in verified_evidence
    )

    def derive(dimension: HardwareAffinityDimension):
        if not verified_evidence:
            return HardwareAffinityLevel.UNKNOWN, ("INSUFFICIENT_EVIDENCE",)

        if dimension in {
            HardwareAffinityDimension.PREFILL_AFFINITY,
            HardwareAffinityDimension.DECODE_AFFINITY,
            HardwareAffinityDimension.EMBEDDING_AFFINITY,
            HardwareAffinityDimension.TRAINING_AFFINITY,
            HardwareAffinityDimension.FINE_TUNING_AFFINITY,
        }:
            if fast_precision:
                return HardwareAffinityLevel.HIGH, ("FAST_PRECISION_CAPABLE",)
            return HardwareAffinityLevel.UNKNOWN, ("PERFORMANCE_EVIDENCE_INSUFFICIENT",)

        if dimension is HardwareAffinityDimension.MEMORY_INTENSITY_TOLERANCE:
            if memory_known:
                if descriptor.memory_capacity_bytes >= 16 * 1024**3:
                    return HardwareAffinityLevel.HIGH, ("VERIFIED_MEMORY_CAPACITY",)
                return HardwareAffinityLevel.MEDIUM, ("VERIFIED_MEMORY_CAPACITY",)
            return HardwareAffinityLevel.UNKNOWN, ("MEMORY_EVIDENCE_INSUFFICIENT",)

        if dimension is HardwareAffinityDimension.COMMUNICATION_INTENSITY_TOLERANCE:
            if p2p:
                return HardwareAffinityLevel.HIGH, ("P2P_CAPABLE",)
            if remote:
                return HardwareAffinityLevel.MEDIUM, ("REMOTE_EXECUTION_CAPABLE",)
            return HardwareAffinityLevel.UNKNOWN, ("INTERCONNECT_EVIDENCE_INSUFFICIENT",)

        if dimension in {
            HardwareAffinityDimension.RETRIEVAL_AFFINITY,
            HardwareAffinityDimension.TOOL_WORKLOAD_AFFINITY,
        }:
            if remote:
                return HardwareAffinityLevel.MEDIUM, ("REMOTE_EXECUTION_CAPABLE",)
            return HardwareAffinityLevel.UNKNOWN, ("RUNTIME_EVIDENCE_INSUFFICIENT",)

        return HardwareAffinityLevel.UNKNOWN, ("INSUFFICIENT_EVIDENCE",)

    result = []
    for dimension in sorted(HardwareAffinityDimension, key=lambda item: item.value):
        level, reasons = derive(dimension)
        result.append(
            HardwareWorkloadAffinity(
                dimension=dimension,
                level=level,
                evidence_record_ids=evidence_ids,
                reason_codes=tuple(sorted(reasons)),
            )
        )
    return tuple(result)
