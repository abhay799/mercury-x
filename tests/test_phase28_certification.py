from mercury.certification.phase28 import evaluate


def test_phase28_executable_certification_passes():
    assert evaluate() is True
