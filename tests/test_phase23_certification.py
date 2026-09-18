from mercury.certification.phase23 import evaluate
def test_phase23_certification_passes():
    assert all(ok for _,ok,_ in evaluate())
