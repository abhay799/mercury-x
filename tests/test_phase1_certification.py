from __future__ import annotations

import pytest
from pydantic import ValidationError

from mercury.certification.phase1 import (
    REQUIRED_PHASE1_GATE_IDS,
    Phase1CertificationConfig,
    Phase1Gate,
    evaluate_phase1_certification,
)


def gates(**overrides: bool) -> tuple[Phase1Gate, ...]:
    return tuple(
        Phase1Gate(
            gate_id=gate_id,
            passed=overrides.get(gate_id, True),
            evidence=f"{gate_id} evidence",
        )
        for gate_id in REQUIRED_PHASE1_GATE_IDS
    )


def config(
    *,
    boundary_violations: tuple[str, ...] = (),
    **overrides: bool,
) -> Phase1CertificationConfig:
    return Phase1CertificationConfig(
        gates=gates(**overrides), boundary_violations=boundary_violations
    )


def test_complete_valid_phase1_evidence_returns_pass():
    result = evaluate_phase1_certification(config())
    assert result.overall_passed is True
    assert result.passed_gate_count == len(REQUIRED_PHASE1_GATE_IDS)


def test_missing_gate_forces_fail():
    result = evaluate_phase1_certification(
        Phase1CertificationConfig(gates=gates()[:-1], boundary_violations=())
    )
    assert result.overall_passed is False
    assert result.missing_gate_ids


def test_failed_gate_forces_fail():
    result = evaluate_phase1_certification(config(gateway_security=False))
    assert result.overall_passed is False
    assert result.failed_gate_count == 1


def test_blank_evidence_is_rejected():
    with pytest.raises(ValidationError):
        Phase1Gate(gate_id="gateway_security", passed=False, evidence=" ")


def test_duplicate_gate_ids_are_rejected():
    item = Phase1Gate(gate_id="gateway_security", passed=True, evidence="verified")
    with pytest.raises(ValidationError):
        Phase1CertificationConfig(gates=(item, item), boundary_violations=())


def test_incomplete_coverage_forces_fail():
    partial = gates()[:3]
    result = evaluate_phase1_certification(
        Phase1CertificationConfig(gates=partial, boundary_violations=())
    )
    assert result.overall_passed is False
    assert len(result.missing_gate_ids) == len(REQUIRED_PHASE1_GATE_IDS) - 3


def test_model_selection_boundary_violation_forces_fail():
    result = evaluate_phase1_certification(
        config(boundary_violations=("model_selection",))
    )
    assert result.overall_passed is False


def test_hardware_selection_boundary_violation_forces_fail():
    result = evaluate_phase1_certification(
        config(boundary_violations=("hardware_selection",))
    )
    assert result.overall_passed is False


def test_workload_intelligence_boundary_violation_forces_fail():
    result = evaluate_phase1_certification(
        config(boundary_violations=("workload_intelligence",))
    )
    assert result.overall_passed is False


def test_execution_graph_or_scheduler_boundary_violation_forces_fail():
    result = evaluate_phase1_certification(
        config(boundary_violations=("execution_graph_or_scheduler",))
    )
    assert result.overall_passed is False


def test_certification_result_is_immutable():
    result = evaluate_phase1_certification(config())
    with pytest.raises((AttributeError, TypeError, ValidationError)):
        result.overall_passed = False


def test_identity_consistency_evidence_is_preserved():
    certification_config = config()
    source = next(
        gate for gate in certification_config.gates if gate.gate_id == "identity_consistency"
    )
    result = evaluate_phase1_certification(certification_config)
    preserved = next(gate for gate in result.gates if gate.gate_id == "identity_consistency")
    assert preserved is source
    assert preserved.evidence == "identity_consistency evidence"


def test_full_suite_evidence_is_preserved():
    certification_config = config()
    source = next(
        gate for gate in certification_config.gates if gate.gate_id == "full_regression_suite"
    )
    result = evaluate_phase1_certification(certification_config)
    preserved = next(gate for gate in result.gates if gate.gate_id == "full_regression_suite")
    assert preserved is source
    assert preserved.evidence == "full_regression_suite evidence"
