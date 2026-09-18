from mercury.certification.phase27 import evaluate


def test_phase27_executable_certification_passes():
    assert evaluate() is True
