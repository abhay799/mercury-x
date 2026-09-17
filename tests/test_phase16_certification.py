from mercury.certification.phase16 import evaluate
def test_phase16_certification():
    assert all(x[1] for x in evaluate())
