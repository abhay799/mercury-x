from mercury.certification.phase19 import evaluate
def test_phase19_certification():
    results=evaluate()
    assert results
    assert all(ok for _,ok,_ in results)
