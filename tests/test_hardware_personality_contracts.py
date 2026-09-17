from mercury.hardware_personality.contracts import (
    CapabilitySupportState,
    HardwareAffinityDimension,
    HardwareAffinityLevel,
    HardwareClass,
    HardwareEvidenceClass,
    HardwarePrecision,
    HardwareTrustState,
)


def test_exact_phase13_enums():
    assert {x.value for x in HardwareClass} == {"CPU","GPU","TPU","NPU","OTHER_ACCELERATOR"}
    assert {x.value for x in HardwareEvidenceClass} == {"DECLARED","PROBED","MEASURED","DERIVED"}
    assert {x.value for x in HardwareTrustState} == {"UNVERIFIED","VERIFIED","STALE","INVALID"}
    assert {x.value for x in CapabilitySupportState} == {"CAPABLE","INCAPABLE","UNKNOWN"}
    assert {x.value for x in HardwarePrecision} == {"FP32","TF32","FP16","BF16","FP8","INT8","INT4"}
    assert {x.value for x in HardwareAffinityLevel} == {"LOW","MEDIUM","HIGH","UNKNOWN"}
    assert len(HardwareAffinityDimension) == 9
