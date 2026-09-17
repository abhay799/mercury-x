from mercury.hardware_personality.affinity import derive_workload_affinities
from mercury.hardware_personality.capabilities import build_capability_matrix
from mercury.hardware_personality.contracts import HardwareClass
from tests._phase13_helpers import descriptor, evidence


def test_accelerator_affinity_is_deterministic():
    desc = descriptor(HardwareClass.GPU)
    ev = (evidence(desc, "precision.FP16", "supported"),)
    caps = build_capability_matrix(ev)
    assert derive_workload_affinities(desc, caps, ev) == derive_workload_affinities(desc, caps, tuple(reversed(ev)))
