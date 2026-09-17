from mercury.certification.phase15 import evaluate
def test_phase15_certification():
    assert all(x[1] for x in evaluate())
