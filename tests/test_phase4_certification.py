import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from mercury.certification.phase4 import (
    KNOWN_PHASE4_BOUNDARY_VIOLATIONS,
    KNOWN_PHASE4_CERTIFICATION_VIOLATIONS,
    REQUIRED_PHASE4_GATE_IDS,
    Phase4CertificationConfig,
    Phase4Gate,
    evaluate_phase4_certification,
)


CONFIG = Path("configs/certification/phase4.json")


def complete_config(**changes: object) -> Phase4CertificationConfig:
    values: dict[str, object] = {
        "gates": tuple(
            Phase4Gate(
                gate_id=gate_id,
                passed=True,
                evidence=f"deterministic evidence for {gate_id}",
            )
            for gate_id in REQUIRED_PHASE4_GATE_IDS
        ),
        "certification_violations": (),
        "boundary_violations": (),
    }
    values.update(changes)
    return Phase4CertificationConfig(**values)


def test_complete_valid_14_gate_certification_passes_deterministically() -> None:
    config = complete_config()
    result = evaluate_phase4_certification(config)
    assert result.overall_passed is True
    assert (result.passed_gate_count, result.failed_gate_count) == (14, 0)
    assert result == evaluate_phase4_certification(config)
    assert result.gates == config.gates


@pytest.mark.parametrize("missing", REQUIRED_PHASE4_GATE_IDS)
def test_every_required_gate_is_required(missing: str) -> None:
    gates = tuple(gate for gate in complete_config().gates if gate.gate_id != missing)
    result = evaluate_phase4_certification(complete_config(gates=gates))
    assert result.overall_passed is False
    assert result.missing_gate_ids == (missing,)


def test_failed_gate_and_incomplete_coverage_fail_closed() -> None:
    failed = tuple(
        gate.model_copy(update={"passed": False})
        if gate.gate_id == "evidence_trust"
        else gate
        for gate in complete_config().gates
    )
    result = evaluate_phase4_certification(complete_config(gates=failed))
    assert result.overall_passed is False
    assert result.failed_gate_count == 1
    assert evaluate_phase4_certification(Phase4CertificationConfig(gates=())).overall_passed is False


def test_blank_evidence_duplicate_unknown_gate_and_malformed_schema_are_rejected() -> None:
    with pytest.raises(ValidationError, match="non-empty"):
        Phase4Gate(gate_id="documentation", passed=True, evidence=" ")
    duplicate = Phase4Gate(gate_id="documentation", passed=True, evidence="docs")
    with pytest.raises(ValueError, match="unique"):
        Phase4CertificationConfig(gates=(duplicate, duplicate))
    with pytest.raises(ValueError, match="unknown"):
        Phase4CertificationConfig(gates=(Phase4Gate(gate_id="unknown", passed=True, evidence="bad"),))
    with pytest.raises(ValidationError):
        Phase4CertificationConfig(schema_version="invalid", gates=())


@pytest.mark.parametrize("violation", sorted(KNOWN_PHASE4_CERTIFICATION_VIOLATIONS))
def test_lifecycle_consistency_and_fail_closed_violations_force_fail(violation: str) -> None:
    result = evaluate_phase4_certification(
        complete_config(certification_violations=(violation,))
    )
    assert result.overall_passed is False
    assert result.certification_violations == (violation,)


@pytest.mark.parametrize("violation", sorted(KNOWN_PHASE4_BOUNDARY_VIOLATIONS))
def test_ranking_selection_assignment_and_execution_leakage_force_fail(violation: str) -> None:
    result = evaluate_phase4_certification(
        complete_config(boundary_violations=(violation,))
    )
    assert result.overall_passed is False
    assert result.boundary_violations == (violation,)


def test_violation_collections_are_unique_known_and_deterministic() -> None:
    with pytest.raises(ValueError, match="unique"):
        complete_config(certification_violations=("identity_inconsistency", "identity_inconsistency"))
    with pytest.raises(ValueError, match="unknown"):
        complete_config(boundary_violations=("unknown_leakage",))
    values = ("status_promotion_inconsistency", "identity_inconsistency")
    assert complete_config(certification_violations=values).certification_violations == tuple(sorted(values))


def test_result_gate_and_evidence_contracts_are_immutable() -> None:
    config = complete_config()
    result = evaluate_phase4_certification(config)
    with pytest.raises((AttributeError, TypeError, ValidationError)):
        result.gates += ()
    with pytest.raises((AttributeError, TypeError, ValidationError)):
        config.gates[0].evidence = "changed"


def test_machine_readable_phase4_config_passes_and_preserves_full_coverage() -> None:
    config = Phase4CertificationConfig.model_validate(
        json.loads(CONFIG.read_text(encoding="utf-8"))
    )
    result = evaluate_phase4_certification(config)
    assert result.overall_passed is True
    assert tuple(gate.gate_id for gate in result.gates) == REQUIRED_PHASE4_GATE_IDS
    assert (result.passed_gate_count, result.failed_gate_count) == (14, 0)
