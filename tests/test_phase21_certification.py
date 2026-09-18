
from mercury.certification.phase21 import evaluate

def test_phase21_executable_certification_passes():
    results = evaluate()
    assert all(ok for _, ok, _ in results)
