from mercury.hardware_personality.capabilities import resolve_capability
from mercury.hardware_personality.contracts import (
    CapabilitySupportState,
    HardwareClass,
    HardwareEvidenceClass,
)
from mercury.hardware_personality.lifecycle import build_hardware_personality_profile
from tests._phase13_helpers import descriptor, evidence


def test_all_hardware_classes_are_representable_without_real_accelerators():
    for hardware_class in HardwareClass:
        desc = descriptor(hardware_class)
        profile = build_hardware_personality_profile(descriptor=desc, evidence=())
        assert profile.descriptor.hardware_class is hardware_class


def test_declared_and_measured_bandwidth_remain_separate():
    from mercury.hardware_personality.contracts import HardwareEvidenceClass
    from tests._phase13_helpers import descriptor, evidence

    desc = descriptor()

    measured = evidence(
        desc,
        "memory.bandwidth_bytes_per_s",
        "80",
        cls=HardwareEvidenceClass.MEASURED,
        sequence=1,
        benchmark_id="bandwidth-bench-1",
    )

    profile = build_hardware_personality_profile(
        descriptor=desc,
        evidence=(measured,),
        declared_memory_bandwidth_bytes_per_s=100,
        measured_memory_bandwidth_bytes_per_s=80,
    )

    assert profile.declared_memory_bandwidth_bytes_per_s == 100
    assert profile.measured_memory_bandwidth_bytes_per_s == 80
    assert profile.declared_memory_bandwidth_bytes_per_s != profile.measured_memory_bandwidth_bytes_per_s



def test_duplicate_or_conflicting_evidence_does_not_create_false_capability():
    desc = descriptor()
    ev = (
        evidence(desc, "precision.INT8", "supported", sequence=1),
        evidence(desc, "precision.INT8", "unsupported", sequence=2),
    )
    result = resolve_capability("precision.INT8", ev)
    assert result.support_state is CapabilitySupportState.UNKNOWN
    assert result.conflict


def test_measured_fixture_is_explicitly_marked_measured():
    desc = descriptor()
    item = evidence(
        desc,
        "benchmark.bandwidth",
        "80",
        cls=HardwareEvidenceClass.MEASURED,
        sequence=1,
        benchmark_id="fixture-benchmark",
    )
    assert item.evidence_class is HardwareEvidenceClass.MEASURED
