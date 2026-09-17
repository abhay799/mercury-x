from mercury.hardware_personality.probes import LocalCPUProbeBackend
from tests._phase13_helpers import descriptor


def test_local_cpu_probe_is_read_only_shape_and_canonical():
    desc = descriptor()
    result = LocalCPUProbeBackend().probe(desc)
    assert result
    assert tuple(item.property_name for item in result) == tuple(sorted(item.property_name for item in result))
    assert all(item.hardware_id == desc.hardware_id for item in result)
