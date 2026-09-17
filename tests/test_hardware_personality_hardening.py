import pytest

from mercury.hardware_personality.affinity import derive_workload_affinities
from mercury.hardware_personality.capabilities import build_capability_matrix
from mercury.hardware_personality.compatibility import (
    evaluate_hardware_compatibility,
    requirement_from_phase12_segment,
)
from mercury.hardware_personality.contracts import (
    HardwareAffinityLevel,
    HardwareDescriptor,
    HardwareEvidenceClass,
    HardwareEvidenceRecord,
    HardwarePersonalityProfile,
    HardwareRequirement,
    HardwareTrustState,
    make_evidence_id,
)
from mercury.hardware_personality.lifecycle import (
    build_hardware_personality_profile,
    transition_hardware_trust,
)
from tests._phase12_helpers import make_segment
from tests._phase13_helpers import descriptor, evidence, profile


def test_affinity_without_verified_evidence_is_unknown():
    desc = descriptor()
    affinities = derive_workload_affinities(desc, build_capability_matrix(()), ())
    assert all(item.level is HardwareAffinityLevel.UNKNOWN for item in affinities)


def test_phase12_opaque_ids_do_not_invent_hardware_semantics():
    segment = make_segment()
    payload = segment.model_dump()
    payload["model_requirement_id"] = "requires-gpu"
    segment = type(segment)(**payload)
    requirement = requirement_from_phase12_segment(segment)
    assert requirement.required_hardware_class is None
    assert requirement.requires_accelerator is None


def test_phase12_explicit_requirement_is_preserved():
    segment = make_segment()
    explicit = HardwareRequirement(requirement_id="explicit", minimum_memory_bytes=4096)
    requirement = requirement_from_phase12_segment(segment, explicit_requirement=explicit)
    assert requirement.minimum_memory_bytes == 4096


def test_measured_bandwidth_requires_matching_measured_evidence():
    desc = descriptor()
    with pytest.raises(ValueError):
        build_hardware_personality_profile(
            descriptor=desc,
            evidence=(),
            measured_memory_bandwidth_bytes_per_s=80,
        )

    ev = evidence(
        desc,
        "memory.bandwidth_bytes_per_s",
        "80",
        cls=HardwareEvidenceClass.MEASURED,
        sequence=1,
        benchmark_id="bench-1",
    )
    profile = build_hardware_personality_profile(
        descriptor=desc,
        evidence=(ev,),
        measured_memory_bandwidth_bytes_per_s=80,
    )
    assert profile.measured_memory_bandwidth_bytes_per_s == 80


def test_forged_verified_profile_without_evidence_is_rejected():
    payload = profile().model_dump()
    payload["evidence_record_ids"] = ()
    payload["profile_fingerprint"] = "forged"

    with pytest.raises(ValueError, match="VERIFIED profile requires evidence"):
        HardwarePersonalityProfile(**payload)


def test_profile_rejects_forged_fingerprint_with_valid_evidence_references():
    payload = profile().model_dump()
    payload["profile_fingerprint"] = "forged"

    with pytest.raises(ValueError, match="profile_fingerprint does not match"):
        HardwarePersonalityProfile(**payload)


def test_descriptor_rejects_forged_hardware_identity():
    payload = descriptor().model_dump()
    payload["hardware_id"] = "forged"

    with pytest.raises(ValueError, match="hardware_id does not match"):
        HardwareDescriptor(**payload)


def test_derived_evidence_requires_explicit_source_evidence_lineage():
    desc = descriptor()
    evidence_id, fingerprint = make_evidence_id(
        hardware_id=desc.hardware_id,
        evidence_class=HardwareEvidenceClass.DERIVED,
        property_name="precision.FP16",
        source_id="deriver",
        sequence=1,
        generation=1,
        observed_value="supported",
    )

    with pytest.raises(ValueError, match="DERIVED evidence requires source evidence lineage"):
        HardwareEvidenceRecord(
            evidence_id=evidence_id,
            hardware_id=desc.hardware_id,
            evidence_class=HardwareEvidenceClass.DERIVED,
            property_name="precision.FP16",
            observed_value="supported",
            source_id="deriver",
            sequence=1,
            generation=1,
            verification_status=True,
            evidence_fingerprint=fingerprint,
        )


def test_profile_rejects_derived_evidence_whose_source_is_not_present():
    desc = descriptor()
    derived_id, derived_fingerprint = make_evidence_id(
        hardware_id=desc.hardware_id,
        evidence_class=HardwareEvidenceClass.DERIVED,
        property_name="precision.FP16",
        source_id="deriver",
        sequence=2,
        generation=1,
        observed_value="supported",
        derived_from_evidence_ids=("missing-source",),
    )
    derived = HardwareEvidenceRecord(
        evidence_id=derived_id,
        hardware_id=desc.hardware_id,
        evidence_class=HardwareEvidenceClass.DERIVED,
        property_name="precision.FP16",
        observed_value="supported",
        source_id="deriver",
        sequence=2,
        generation=1,
        verification_status=True,
        evidence_fingerprint=derived_fingerprint,
        derived_from_evidence_ids=("missing-source",),
    )
    with pytest.raises(ValueError, match="derived evidence source missing"):
        build_hardware_personality_profile(descriptor=desc, evidence=(derived,))


def test_declared_evidence_cannot_claim_an_observation():
    desc = descriptor()
    evidence_id, fingerprint = make_evidence_id(
        hardware_id=desc.hardware_id,
        evidence_class=HardwareEvidenceClass.DECLARED,
        property_name="precision.FP16",
        source_id="declaration",
        sequence=1,
        generation=1,
        declared_value="supported",
        observed_value="supported",
    )

    with pytest.raises(ValueError, match="DECLARED evidence must not include observed_value"):
        HardwareEvidenceRecord(
            evidence_id=evidence_id,
            hardware_id=desc.hardware_id,
            evidence_class=HardwareEvidenceClass.DECLARED,
            property_name="precision.FP16",
            declared_value="supported",
            observed_value="supported",
            source_id="declaration",
            sequence=1,
            generation=1,
            verification_status=False,
            evidence_fingerprint=fingerprint,
        )


def test_compatibility_rejects_stale_profile():
    stale = transition_hardware_trust(profile(), HardwareTrustState.STALE)
    result = evaluate_hardware_compatibility(
        stale,
        HardwareRequirement(requirement_id="trusted-profile-required"),
    )

    assert result.state.value == "INCOMPATIBLE"
    assert result.reason_codes == ("PROFILE_TRUST_NOT_VERIFIED",)


def test_compatibility_rejects_raw_profile_with_invalid_fingerprint():
    valid = profile()
    payload = {
        field_name: getattr(valid, field_name)
        for field_name in type(valid).model_fields
    }
    payload["profile_fingerprint"] = "forged"
    forged = HardwarePersonalityProfile.model_construct(**payload)

    result = evaluate_hardware_compatibility(
        forged,
        HardwareRequirement(requirement_id="integrity-required"),
    )

    assert result.state.value == "INCOMPATIBLE"
    assert result.reason_codes == ("PROFILE_INTEGRITY_INVALID",)


def test_verified_profile_requires_verified_source_evidence():
    desc = descriptor()
    unverified = evidence(desc, "precision.FP32", "supported", verified=False)

    with pytest.raises(ValueError, match="VERIFIED profile requires verified evidence"):
        build_hardware_personality_profile(
            descriptor=desc,
            evidence=(unverified,),
            trust_state=HardwareTrustState.VERIFIED,
        )
