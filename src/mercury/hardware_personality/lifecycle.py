import hashlib
import json

from mercury.hardware_personality.affinity import derive_workload_affinities
from mercury.hardware_personality.capabilities import build_capability_matrix
from mercury.hardware_personality.contracts import (
    CapabilitySupportState,
    HardwareEvidenceClass,
    HardwareEvidenceRecord,
    HardwarePersonalityProfile,
    HardwarePrecision,
    HardwareTrustState,
    make_profile_identity,
)


def _fingerprint(payload) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _require_measured_bandwidth_evidence(evidence, measured_value):
    if measured_value is None:
        return
    matches = [
        item for item in evidence
        if item.evidence_class is HardwareEvidenceClass.MEASURED
        and item.property_name == "memory.bandwidth_bytes_per_s"
        and item.verification_status
        and item.observed_value == str(measured_value)
        and item.benchmark_id
    ]
    if not matches:
        raise ValueError("measured memory bandwidth requires matching verified MEASURED evidence")


def build_hardware_personality_profile(
    *,
    descriptor,
    evidence: tuple[HardwareEvidenceRecord, ...],
    profile_generation: int = 1,
    trust_state: HardwareTrustState = HardwareTrustState.UNVERIFIED,
    declared_memory_bandwidth_bytes_per_s=None,
    measured_memory_bandwidth_bytes_per_s=None,
    interconnect_capabilities=(),
    runtime_capabilities=(),
    software_stack=(),
    power_constraints=(),
) -> HardwarePersonalityProfile:
    evidence = tuple(sorted(evidence, key=lambda item: item.evidence_id))
    if any(item.hardware_id != descriptor.hardware_id for item in evidence):
        raise ValueError("evidence hardware mismatch")

    _require_measured_bandwidth_evidence(evidence, measured_memory_bandwidth_bytes_per_s)

    capabilities = build_capability_matrix(evidence)
    affinities = derive_workload_affinities(descriptor, capabilities, evidence)
    supported = tuple(sorted(
        (
            precision
            for precision in HardwarePrecision
            if any(
                item.property_name == f"precision.{precision.value}"
                and item.support_state is CapabilitySupportState.CAPABLE
                for item in capabilities
            )
        ),
        key=lambda item: item.value,
    ))
    hardware_profile_id = make_profile_identity(
        hardware_id=descriptor.hardware_id,
        profile_generation=profile_generation,
    )

    body = {
        "hardware_profile_id": hardware_profile_id,
        "descriptor": descriptor.model_dump(mode="json"),
        "capabilities": [item.model_dump(mode="json") for item in capabilities],
        "supported_precisions": [item.value for item in supported],
        "declared_memory_bandwidth_bytes_per_s": declared_memory_bandwidth_bytes_per_s,
        "measured_memory_bandwidth_bytes_per_s": measured_memory_bandwidth_bytes_per_s,
        "interconnect_capabilities": sorted(set(interconnect_capabilities)),
        "runtime_capabilities": sorted(set(runtime_capabilities)),
        "software_stack": sorted(set(software_stack)),
        "power_constraints": sorted(set(power_constraints)),
        "evidence_record_ids": [item.evidence_id for item in evidence],
        "workload_affinities": [item.model_dump(mode="json") for item in affinities],
        "profile_generation": profile_generation,
        "trust_state": trust_state.value,
    }
    fp = _fingerprint(body)

    return HardwarePersonalityProfile(
        hardware_profile_id=hardware_profile_id,
        descriptor=descriptor,
        capabilities=capabilities,
        supported_precisions=supported,
        declared_memory_bandwidth_bytes_per_s=declared_memory_bandwidth_bytes_per_s,
        measured_memory_bandwidth_bytes_per_s=measured_memory_bandwidth_bytes_per_s,
        interconnect_capabilities=tuple(sorted(set(interconnect_capabilities))),
        runtime_capabilities=tuple(sorted(set(runtime_capabilities))),
        software_stack=tuple(sorted(set(software_stack))),
        power_constraints=tuple(sorted(set(power_constraints))),
        evidence_record_ids=tuple(item.evidence_id for item in evidence),
        workload_affinities=affinities,
        profile_generation=profile_generation,
        profile_fingerprint=fp,
        trust_state=trust_state,
    )


_ALLOWED = {
    HardwareTrustState.UNVERIFIED: {HardwareTrustState.VERIFIED, HardwareTrustState.INVALID},
    HardwareTrustState.VERIFIED: {HardwareTrustState.STALE, HardwareTrustState.INVALID},
    HardwareTrustState.STALE: {HardwareTrustState.VERIFIED, HardwareTrustState.INVALID},
}


def _refingerprint(profile, target):
    payload = profile.model_dump()
    payload["trust_state"] = target
    payload["profile_fingerprint"] = ""
    body = dict(payload)
    body["profile_fingerprint"] = None
    payload["profile_fingerprint"] = _fingerprint(body)
    return HardwarePersonalityProfile(**payload)


def transition_hardware_trust(profile, target: HardwareTrustState):
    if target not in _ALLOWED.get(profile.trust_state, set()):
        raise ValueError("forbidden hardware trust transition")
    return _refingerprint(profile, target)


def evaluate_profile_staleness(
    profile: HardwarePersonalityProfile,
    *,
    current_generation: int,
    max_generation_age: int,
) -> bool:
    if current_generation < profile.profile_generation:
        raise ValueError("current_generation precedes profile generation")
    if max_generation_age < 0:
        raise ValueError("max_generation_age must be nonnegative")
    return (current_generation - profile.profile_generation) > max_generation_age


def refresh_hardware_profile(
    profile: HardwarePersonalityProfile,
    *,
    evidence: tuple[HardwareEvidenceRecord, ...],
    trust_state: HardwareTrustState = HardwareTrustState.UNVERIFIED,
):
    return build_hardware_personality_profile(
        descriptor=profile.descriptor,
        evidence=evidence,
        profile_generation=profile.profile_generation + 1,
        trust_state=trust_state,
        declared_memory_bandwidth_bytes_per_s=profile.declared_memory_bandwidth_bytes_per_s,
        measured_memory_bandwidth_bytes_per_s=profile.measured_memory_bandwidth_bytes_per_s,
        interconnect_capabilities=profile.interconnect_capabilities,
        runtime_capabilities=profile.runtime_capabilities,
        software_stack=profile.software_stack,
        power_constraints=profile.power_constraints,
    )
