import pytest

from mercury.hardware_personality.contracts import HardwareClass
from mercury.hardware_personality.normalization import normalize_hardware_descriptor


def test_normalization_is_deterministic():
    raw = {
        "hardware_class": "cpu",
        "vendor": "  Generic  ",
        "architecture": " x86_64 ",
        "device_family": " CPU ",
        "device_model": " test ",
        "memory_capacity_bytes": 1024,
    }
    a = normalize_hardware_descriptor(raw)
    b = normalize_hardware_descriptor(dict(raw))
    assert a == b
    assert a.hardware_class is HardwareClass.CPU


def test_missing_descriptor_field_fails_closed():
    with pytest.raises(ValueError):
        normalize_hardware_descriptor({"hardware_class": "CPU"})
