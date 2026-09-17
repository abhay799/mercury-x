import pytest

from mercury.hardware_personality.affinity import derive_workload_affinities
from mercury.hardware_personality.capabilities import build_capability_matrix
from mercury.hardware_personality.compatibility import requirement_from_phase12_segment
from mercury.hardware_personality.contracts import (
    HardwareAffinityLevel,
    HardwareEvidenceClass,
    HardwareRequirement,
)
from mercury.hardware_personality.lifecycle import build_hardware_personality_profile
from tests._phase12_helpers import make_segment
from tests._phase13_helpers import descriptor, evidence


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
