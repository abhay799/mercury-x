import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from mercury.certification.phase3 import REQUIRED_PHASE3_GATE_IDS, Phase3CertificationConfig, Phase3Gate, evaluate_phase3_certification


CONFIG = Path("configs/certification/phase3.json")


def complete_config(**changes: object) -> Phase3CertificationConfig:
    values: dict[str, object] = {
        "gates": tuple(Phase3Gate(gate_id=gate_id, passed=True, evidence=f"deterministic evidence for {gate_id}") for gate_id in REQUIRED_PHASE3_GATE_IDS),
        "boundary_violations": (),
    }
    values.update(changes)
    return Phase3CertificationConfig(**values)


def test_complete_valid_15_gate_certification_passes_deterministically() -> None:
    config = complete_config()
    result = evaluate_phase3_certification(config)
    assert result.overall_passed is True
    assert (result.passed_gate_count, result.failed_gate_count) == (15, 0)
    assert result == evaluate_phase3_certification(config)
    assert result.gates == config.gates


@pytest.mark.parametrize("missing", REQUIRED_PHASE3_GATE_IDS)
def test_every_required_gate_is_required(missing: str) -> None:
    gates = tuple(gate for gate in complete_config().gates if gate.gate_id != missing)
    result = evaluate_phase3_certification(complete_config(gates=gates))
    assert result.overall_passed is False
    assert missing in result.missing_gate_ids


def test_failed_gate_incomplete_config_and_malformed_schema_fail_closed() -> None:
    failed = tuple(gate.model_copy(update={"passed": False}) if gate.gate_id == "graph_readiness" else gate for gate in complete_config().gates)
    assert evaluate_phase3_certification(complete_config(gates=failed)).overall_passed is False
    assert evaluate_phase3_certification(Phase3CertificationConfig(gates=())).overall_passed is False
    with pytest.raises(ValidationError):
        Phase3CertificationConfig(schema_version="invalid", gates=())


def test_blank_evidence_and_duplicate_ids_are_rejected() -> None:
    with pytest.raises(ValidationError, match="non-empty"):
        Phase3Gate(gate_id="documentation", passed=True, evidence=" ")
    duplicate = Phase3Gate(gate_id="documentation", passed=True, evidence="docs")
    with pytest.raises(ValueError, match="unique"):
        Phase3CertificationConfig(gates=(duplicate, duplicate))


@pytest.mark.parametrize(
    "violation",
    ["model_selection", "provider_selection", "hardware_selection", "placement_selection", "scheduler_or_runtime", "precision_migration_or_speculation", "nested_boundary_leakage"],
)
def test_direct_and_nested_boundary_leakage_forces_fail(violation: str) -> None:
    result = evaluate_phase3_certification(complete_config(boundary_violations=(violation,)))
    assert result.overall_passed is False
    assert result.boundary_violations == (violation,)


def test_gate_and_evidence_contracts_are_immutable() -> None:
    config = complete_config()
    result = evaluate_phase3_certification(config)
    with pytest.raises((AttributeError, TypeError, ValidationError)):
        result.gates += ()
    with pytest.raises((AttributeError, TypeError, ValidationError)):
        config.gates[0].evidence = "changed"


def test_machine_readable_phase3_config_passes_and_preserves_full_coverage() -> None:
    config = Phase3CertificationConfig.model_validate(json.loads(CONFIG.read_text(encoding="utf-8")))
    result = evaluate_phase3_certification(config)
    assert result.overall_passed is True
    assert tuple(gate.gate_id for gate in result.gates) == REQUIRED_PHASE3_GATE_IDS
