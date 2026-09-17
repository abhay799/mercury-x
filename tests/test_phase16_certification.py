import pytest

from mercury.certification import phase16


def test_phase16_certification():
    assert all(x[1] for x in phase16.evaluate())


def test_phase16_certification_does_not_hardcode_gate_success(monkeypatch) -> None:
    monkeypatch.setitem(phase16.CHECKS, "states", lambda: (False, "forced failure"))

    assert not all(result[1] for result in phase16.evaluate())
