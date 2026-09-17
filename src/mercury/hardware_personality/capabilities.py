from mercury.hardware_personality.contracts import (
    CapabilityAssessment,
    CapabilitySupportState,
    HardwareEvidenceRecord,
    HardwarePrecision,
)


_TRUE = {"true", "1", "yes", "supported", "capable"}
_FALSE = {"false", "0", "no", "unsupported", "incapable"}


def _parse_support(value: str | None):
    if value is None:
        return None
    lowered = value.strip().lower()
    if lowered in _TRUE:
        return True
    if lowered in _FALSE:
        return False
    return None


def resolve_capability(
    property_name: str,
    evidence: tuple[HardwareEvidenceRecord, ...],
) -> CapabilityAssessment:
    relevant = tuple(sorted(
        (item for item in evidence if item.property_name == property_name),
        key=lambda item: item.evidence_id,
    ))
    ids = tuple(item.evidence_id for item in relevant)

    if not relevant:
        return CapabilityAssessment(
            property_name=property_name,
            support_state=CapabilitySupportState.UNKNOWN,
            evidence_record_ids=(),
        )

    votes = []
    for item in relevant:
        raw = item.observed_value if item.observed_value is not None else item.declared_value
        parsed = _parse_support(raw)
        if parsed is not None and item.verification_status:
            votes.append(parsed)

    if True in votes and False in votes:
        return CapabilityAssessment(
            property_name=property_name,
            support_state=CapabilitySupportState.UNKNOWN,
            evidence_record_ids=ids,
            conflict=True,
            conflict_reason="CONFLICTING_VERIFIED_EVIDENCE",
        )
    if True in votes:
        state = CapabilitySupportState.CAPABLE
    elif False in votes:
        state = CapabilitySupportState.INCAPABLE
    else:
        state = CapabilitySupportState.UNKNOWN

    return CapabilityAssessment(
        property_name=property_name,
        support_state=state,
        evidence_record_ids=ids,
    )


def build_capability_matrix(
    evidence: tuple[HardwareEvidenceRecord, ...],
) -> tuple[CapabilityAssessment, ...]:
    names = {
        *(f"precision.{precision.value}" for precision in HardwarePrecision),
        "acceleration.tensor_core_like",
        "interconnect.peer_to_peer",
        "memory.unified",
        "runtime.remote_execution",
        "virtualization.supported",
        "partitioning.supported",
    }
    names.update(item.property_name for item in evidence if item.property_name.startswith(("runtime.", "software.", "interconnect.")))
    return tuple(resolve_capability(name, evidence) for name in sorted(names))
