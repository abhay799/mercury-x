from mercury.certification.phase25 import evaluate
def test_phase25_certification_passes():
    assert all(ok for _,ok,_ in evaluate())
