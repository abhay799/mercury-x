from mercury.hardware_personality.capabilities import resolve_capability
from mercury.hardware_personality.contracts import CapabilitySupportState
from tests._phase13_helpers import descriptor, evidence


def test_missing_evidence_is_unknown():
    assert resolve_capability("precision.FP16", ()).support_state is CapabilitySupportState.UNKNOWN


def test_conflicting_verified_evidence_stays_unknown():
    desc = descriptor()
    ev = (
        evidence(desc, "precision.BF16", "supported", sequence=1),
        evidence(desc, "precision.BF16", "unsupported", sequence=2),
    )
    result = resolve_capability("precision.BF16", ev)
    assert result.support_state is CapabilitySupportState.UNKNOWN
    assert result.conflict
