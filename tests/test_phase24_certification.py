from mercury.certification.phase24 import evaluate
def test_phase24_certification_passes():
    assert all(ok for _,ok,_ in evaluate())
