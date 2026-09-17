from mercury.certification.phase14 import evaluate
def test_phase14_certification():
    assert all(ok for _,ok,_ in evaluate())
