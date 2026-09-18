from mercury.certification import phase17
from mercury.certification import phase17_checks
from mercury.reasoning_budget.lifecycle import build_reasoning_budget


def test_phase17_certification():
    results = phase17.evaluate()
    assert results
    assert all(ok for _, ok, _ in results)
    assert len({id(check) for check in phase17.CHECKS.values()}) == len(phase17.CHECKS)
    assert len({evidence for _, _, evidence in results}) == len(results)


def test_phase17_quality_floor_gate_fails_independently(monkeypatch):
    real = phase17_checks.build_reasoning_budget

    def accept_below(request, candidate, generation=1):
        if candidate.expected_quality_low is not None and candidate.expected_quality_low < request.quality_floor:
            candidate = candidate.model_copy(update={
                "expected_quality_low": request.quality_floor,
                "expected_quality_high": request.quality_floor,
            })
        return real(request, candidate, generation=generation)

    monkeypatch.setattr(phase17_checks, "build_reasoning_budget", accept_below)
    assert not phase17_checks.quality_floor()[0]
    assert phase17_checks.contracts()[0]
    assert phase17_checks.uncalibrated()[0]


def test_phase17_uncalibrated_gate_fails_independently(monkeypatch):
    class PermissiveEstimate:
        def __init__(self, **kwargs):
            self.calibration_state = kwargs.get("calibration_state")
            self.calibration_artifact_id = kwargs.get("calibration_artifact_id")
            self.backend_kind = kwargs.get("backend_kind")

    monkeypatch.setattr(phase17_checks, "ReasoningCostEstimate", PermissiveEstimate)
    assert not phase17_checks.uncalibrated()[0]
    assert phase17_checks.contracts()[0]
    assert phase17_checks.quality_floor()[0]


def test_phase17_contracts_gate_fails_independently(monkeypatch):
    monkeypatch.setattr(phase17_checks.ReasoningBudget, "model_validate", lambda payload: payload)
    assert not phase17_checks.contracts()[0]
    assert phase17_checks.quality_floor()[0]
    assert phase17_checks.uncalibrated()[0]
    assert build_reasoning_budget is not None
