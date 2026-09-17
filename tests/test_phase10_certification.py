import pytest

from mercury.certification.phase10 import (
    REQUIRED_PHASE10_GATE_IDS,
    Phase10CertificationConfig,
    Phase10Gate,
    evaluate_phase10_certification,
)


def complete():
    return Phase10CertificationConfig(
        gates=tuple(
            Phase10Gate(gate_id=gate_id, passed=True, evidence="verified")
            for gate_id in REQUIRED_PHASE10_GATE_IDS
        )
    )


def test_complete_config_passes():
    result = evaluate_phase10_certification(complete())
    assert result.overall_passed
    assert result.failed_gate_count == 0
    assert result.missing_gate_ids == ()


def test_missing_gate_fails_closed():
    result = evaluate_phase10_certification(
        Phase10CertificationConfig(gates=complete().gates[:-1])
    )
    assert not result.overall_passed


def test_failed_gate_fails_closed():
    gates = list(complete().gates)
    gates[0] = Phase10Gate(
        gate_id=gates[0].gate_id,
        passed=False,
        evidence="failed",
    )
    assert not evaluate_phase10_certification(
        Phase10CertificationConfig(gates=tuple(gates))
    ).overall_passed


def test_unknown_duplicate_blank_and_nonconfig_fail_closed():
    with pytest.raises(Exception):
        Phase10CertificationConfig(
            gates=(Phase10Gate(gate_id="unknown", passed=True, evidence="x"),)
        )
    gate = Phase10Gate(
        gate_id=REQUIRED_PHASE10_GATE_IDS[0],
        passed=True,
        evidence="x",
    )
    with pytest.raises(Exception):
        Phase10CertificationConfig(gates=(gate, gate))
    with pytest.raises(Exception):
        Phase10Gate(
            gate_id=REQUIRED_PHASE10_GATE_IDS[0],
            passed=True,
            evidence="",
        )
    with pytest.raises(ValueError):
        evaluate_phase10_certification({"gates": []})
