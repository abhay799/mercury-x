from mercury.certification.phase17 import evaluate
def test_phase17_certification():
    results=evaluate()
    assert results
    assert all(ok for _,ok,_ in results)
