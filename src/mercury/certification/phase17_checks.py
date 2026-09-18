from mercury.reasoning_budget.contracts import (
    BudgetCalibrationState,
    ReasoningBudget,
    ReasoningBudgetCandidate,
    ReasoningBudgetRequest,
)
from mercury.reasoning_budget.control import evaluate_escalation
from mercury.reasoning_budget.cost import (
    DeterministicReasoningCostBackend,
    ReasoningBackendKind,
    ReasoningCostEstimate,
)
from mercury.reasoning_budget.frontier import build_budget_frontier
from mercury.reasoning_budget.lifecycle import build_reasoning_budget


def _raises(operation):
    try:
        operation()
    except ValueError:
        return True
    return False


def _request():
    return ReasoningBudgetRequest(
        request_id="r", workload_id="w", segment_id="s", requirement_interface_id="req",
        quality_metric_id="q", quality_floor=.9, confidence_floor=.8, max_reasoning_steps=8,
        max_tokens=4096, max_compute_units=20, max_speculative_branches=3, verification_depth_min=1,
        latency_ceiling_ms=2000, escalation_policy_id="escalate", stop_policy_id="stop",
        provenance_ids=("cert",),
    )


def _candidate(**updates):
    values = dict(
        candidate_id="c", reasoning_steps=4, max_tokens=2048, compute_units=10, verification_depth=1,
        speculation_width=2, expected_quality_low=.92, expected_quality_high=.95,
        expected_latency_ms=1000, uncertainty=.2, evidence_ids=("e",),
    )
    values.update(updates)
    return ReasoningBudgetCandidate(**values)


def contracts():
    request = _request()
    budget = build_reasoning_budget(request, _candidate())
    duplicate = _raises(lambda: ReasoningBudgetRequest(
        request_id="r", workload_id="w", segment_id="s", requirement_interface_id="req",
        quality_metric_id="q", quality_floor=.9, confidence_floor=.8, max_reasoning_steps=8,
        max_tokens=4096, max_compute_units=20, max_speculative_branches=3, verification_depth_min=1,
        latency_ceiling_ms=2000, escalation_policy_id="escalate", stop_policy_id="stop",
        provenance_ids=("cert", "cert"),
    ))
    blank = _raises(lambda: ReasoningBudgetRequest(
        request_id=" ", workload_id="w", segment_id="s", requirement_interface_id="req",
        quality_metric_id="q", quality_floor=.9, confidence_floor=.8, max_reasoning_steps=8,
        max_tokens=4096, max_compute_units=20, max_speculative_branches=3, verification_depth_min=1,
        latency_ceiling_ms=2000, escalation_policy_id="escalate", stop_policy_id="stop",
        provenance_ids=("cert",),
    ))
    forged = _raises(lambda: ReasoningBudget.model_validate(budget.model_dump() | {"fingerprint": "0" * 64}))
    ok = bool(request.request_id) and duplicate and blank and forged
    return ok, "budget contracts reject blank identity, duplicate provenance, and forged fingerprints"


def quality_floor():
    request = _request()
    budget = build_reasoning_budget(request, _candidate())
    below = _raises(lambda: build_reasoning_budget(request, _candidate(expected_quality_low=.8, expected_quality_high=.81)))
    ok = budget.quality_floor == request.quality_floor and below
    return ok, "budget preserves the hard quality floor and rejects below-floor candidates"


def frontier():
    dominated = _candidate(candidate_id="dominated", expected_quality_low=.9, expected_quality_high=.91, compute_units=20)
    dominant = _candidate(candidate_id="dominant", expected_quality_low=.92, expected_quality_high=.95, compute_units=10)
    result = build_budget_frontier((dominated, dominant))
    ok = tuple(item.candidate_id for item in result) == ("dominant",)
    return ok, "frontier executable"


def escalation():
    yes, reasons = evaluate_escalation(
        quality_met=False, confidence_met=True, verification_passed=True,
        uncertainty_ok=True, branches_agree=True, hard_ceiling_reached=False,
    )
    stop, _ = evaluate_escalation(
        quality_met=True, confidence_met=True, verification_passed=True,
        uncertainty_ok=True, branches_agree=True, hard_ceiling_reached=False,
    )
    return yes and "QUALITY_SHORTFALL" in reasons and not stop, "escalation executable"


def uncalibrated():
    estimate = DeterministicReasoningCostBackend().estimate(
        steps=4, tokens=1024, verification_depth=1, speculation_width=2, evidence_ids=("cost",),
    )
    honest = (
        estimate.calibration_state is BudgetCalibrationState.UNCALIBRATED
        and estimate.calibration_artifact_id is None
        and estimate.backend_kind is ReasoningBackendKind.DETERMINISTIC
    )
    empirical = _raises(lambda: ReasoningCostEstimate(
        estimate_id="bad", compute_units=1, token_units=1, verification_units=0, speculation_units=0,
        retry_units=0, aggregation_units=0, backend_id="empirical", backend_version="1",
        backend_kind=ReasoningBackendKind.EMPIRICAL, operating_domain="fixture", uncertainty=.1,
        calibration_state=BudgetCalibrationState.EMPIRICALLY_CALIBRATED,
    ))
    claimed = _raises(lambda: ReasoningCostEstimate(
        estimate_id="claimed", compute_units=1, token_units=1, verification_units=0, speculation_units=0,
        retry_units=0, aggregation_units=0, backend_id="deterministic-reasoning-cost", backend_version="v1",
        backend_kind=ReasoningBackendKind.DETERMINISTIC, operating_domain="fixture", uncertainty=1,
        calibration_state=BudgetCalibrationState.UNCALIBRATED, calibration_artifact_id="artifact",
    ))
    return honest and empirical and claimed, "deterministic cost remains UNCALIBRATED and empirical claims fail closed"


def boundary():
    import inspect
    import mercury.reasoning_budget.lifecycle as module
    source = inspect.getsource(module)
    return not any(token in source for token in ("schedule(", "migrate(", "provision(", "select_model")), "no forbidden authority"


CHECKS = {
    "contracts": contracts,
    "quality_floor": quality_floor,
    "frontier": frontier,
    "escalation": escalation,
    "uncalibrated": uncalibrated,
    "no_cross_phase_authority": boundary,
}
