from mercury.certification.phase26 import evaluate


def test_phase26_executable_certification_passes():
    assert evaluate() is True
