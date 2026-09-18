from mercury.certification.phase30 import evaluate


def test_phase30_executable_certification_passes():
    assert evaluate() is True
