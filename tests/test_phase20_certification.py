from mercury.certification.phase20 import evaluate
def test_phase20_certification():
    results=evaluate()
    assert results
    assert all(ok for _,ok,_ in results)
