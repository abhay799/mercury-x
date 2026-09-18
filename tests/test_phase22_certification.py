from mercury.certification.phase22 import evaluate
def test_phase22_certification_passes():
    assert all(ok for _,ok,_ in evaluate())
