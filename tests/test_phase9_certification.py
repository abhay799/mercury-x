import pytest

from mercury.certification.phase9 import (
    REQUIRED_PHASE9_GATE_IDS,
    Phase9CertificationConfig,
    Phase9Gate,
    evaluate_phase9_certification,
)


def complete():
    return Phase9CertificationConfig(
        gates=tuple(
            Phase9Gate(
                gate_id=gate_id,
                passed=True,
                evidence="verified",
            )
            for gate_id
            in REQUIRED_PHASE9_GATE_IDS
        )
    )


def test_complete_config_passes_all_required_gates():
    result = evaluate_phase9_certification(
        complete()
    )

    assert result.overall_passed
    assert result.passed_gate_count == len(
        REQUIRED_PHASE9_GATE_IDS
    )
    assert result.failed_gate_count == 0
    assert result.missing_gate_ids == ()


def test_missing_gate_fails_closed():
    config = Phase9CertificationConfig(
        gates=complete().gates[:-1]
    )

    result = evaluate_phase9_certification(
        config
    )

    assert not result.overall_passed
    assert result.missing_gate_ids == (
        REQUIRED_PHASE9_GATE_IDS[-1],
    )


def test_failed_gate_fails_closed():
    gates = list(
        complete().gates
    )

    gates[0] = Phase9Gate(
        gate_id=gates[0].gate_id,
        passed=False,
        evidence="verification failed",
    )

    result = evaluate_phase9_certification(
        Phase9CertificationConfig(
            gates=tuple(gates)
        )
    )

    assert not result.overall_passed
    assert result.failed_gate_count == 1


def test_unknown_gate_rejected():
    with pytest.raises(
        ValueError
    ):
        Phase9CertificationConfig(
            gates=(
                Phase9Gate(
                    gate_id="unknown",
                    passed=True,
                    evidence="invalid",
                ),
            )
        )


def test_duplicate_gate_rejected():
    gate = Phase9Gate(
        gate_id=REQUIRED_PHASE9_GATE_IDS[0],
        passed=True,
        evidence="verified",
    )

    with pytest.raises(
        ValueError
    ):
        Phase9CertificationConfig(
            gates=(
                gate,
                gate,
            )
        )


def test_blank_evidence_rejected():
    with pytest.raises(
        ValueError
    ):
        Phase9Gate(
            gate_id=REQUIRED_PHASE9_GATE_IDS[0],
            passed=True,
            evidence="",
        )


def test_non_config_input_rejected():
    with pytest.raises(
        ValueError
    ):
        evaluate_phase9_certification(
            {
                "gates": []
            }
        )