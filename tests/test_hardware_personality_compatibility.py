from mercury.hardware_personality.compatibility import evaluate_hardware_compatibility
from mercury.hardware_personality.contracts import (
    HardwareCompatibilityState,
    HardwarePrecision,
    HardwareRequirement,
)
from tests._phase13_helpers import profile


def test_explicit_requirement_compatibility():
    p = profile()
    req = HardwareRequirement(
        requirement_id="r1",
        required_precision=HardwarePrecision.FP32,
        minimum_memory_bytes=1024,
    )
    result = evaluate_hardware_compatibility(p, req)
    assert result.state is HardwareCompatibilityState.COMPATIBLE


def test_unknown_precision_remains_unknown():
    p = profile()
    req = HardwareRequirement(
        requirement_id="r2",
        required_precision=HardwarePrecision.FP8,
    )
    result = evaluate_hardware_compatibility(p, req)
    assert result.state is HardwareCompatibilityState.UNKNOWN
