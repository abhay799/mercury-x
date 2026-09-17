import pytest

from mercury.hardware_personality.contracts import HardwareTrustState
from mercury.hardware_personality.lifecycle import (
    evaluate_profile_staleness,
    refresh_hardware_profile,
    transition_hardware_trust,
)
from tests._phase13_helpers import profile


def test_trust_transition_and_invalid_terminality():
    p = profile()
    stale = transition_hardware_trust(p, HardwareTrustState.STALE)
    invalid = transition_hardware_trust(stale, HardwareTrustState.INVALID)
    assert invalid.trust_state is HardwareTrustState.INVALID
    with pytest.raises(ValueError):
        transition_hardware_trust(invalid, HardwareTrustState.VERIFIED)


def test_staleness_is_generation_based():
    p = profile()
    assert not evaluate_profile_staleness(p, current_generation=2, max_generation_age=1)
    assert evaluate_profile_staleness(p, current_generation=3, max_generation_age=1)


def test_refresh_creates_new_generation():
    p = profile()
    refreshed = refresh_hardware_profile(p, evidence=())
    assert refreshed.profile_generation == p.profile_generation + 1
    assert refreshed.hardware_profile_id != p.hardware_profile_id
