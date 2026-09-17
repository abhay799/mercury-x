from mercury.certification.phase18 import evaluate
def test_phase18_certification():
    results=evaluate()
    assert results
    assert all(ok for _,ok,_ in results)
