import pytest

from mercury.certification.phase11 import (
    REQUIRED_PHASE11_GATE_IDS,
    Phase11CertificationConfig,
    Phase11Gate,
    evaluate_phase11_certification,
)


def complete():
    return Phase11CertificationConfig(
        gates=tuple(
            Phase11Gate(gate_id=gate_id, passed=True, evidence="verified")
            for gate_id in REQUIRED_PHASE11_GATE_IDS
        )
    )


def test_complete_config_passes():
    result = evaluate_phase11_certification(complete())
    assert result.overall_passed
    assert result.failed_gate_count == 0
    assert result.missing_gate_ids == ()


def test_missing_failed_unknown_duplicate_blank_and_nonconfig_fail_closed():
    assert not evaluate_phase11_certification(
        Phase11CertificationConfig(gates=complete().gates[:-1])
    ).overall_passed

    gates = list(complete().gates)
    gates[0] = Phase11Gate(gate_id=gates[0].gate_id, passed=False, evidence="failed")
    assert not evaluate_phase11_certification(
        Phase11CertificationConfig(gates=tuple(gates))
    ).overall_passed

    with pytest.raises(Exception):
        Phase11CertificationConfig(
            gates=(Phase11Gate(gate_id="unknown", passed=True, evidence="x"),)
        )

    gate = complete().gates[0]
    with pytest.raises(Exception):
        Phase11CertificationConfig(gates=(gate, gate))

    with pytest.raises(Exception):
        Phase11Gate(
            gate_id=REQUIRED_PHASE11_GATE_IDS[0],
            passed=True,
            evidence="",
        )

    with pytest.raises(ValueError):
        evaluate_phase11_certification({"gates": []})
