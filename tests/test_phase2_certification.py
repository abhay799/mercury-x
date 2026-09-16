import json
from dataclasses import dataclass
from pathlib import Path

import pytest
from pydantic import ValidationError

from mercury.certification.phase2 import (
    REQUIRED_PHASE2_GATE_IDS,
    Phase2CertificationConfig,
    Phase2Gate,
    evaluate_phase2_certification,
)


CONFIG = Path("configs/certification/phase2.json")


def complete_config(**changes: object) -> Phase2CertificationConfig:
    values: dict[str, object] = {
        "gates": tuple(Phase2Gate(gate_id=gate_id, passed=True, evidence=f"evidence for {gate_id}") for gate_id in REQUIRED_PHASE2_GATE_IDS),
        "boundary_violations": (),
    }
    values.update(changes)
    return Phase2CertificationConfig(**values)


def test_complete_valid_certification_returns_pass_and_preserves_all_gates() -> None:
    config = complete_config()
    result = evaluate_phase2_certification(config)

    assert result.overall_passed is True
    assert result.passed_gate_count == 13
    assert result.failed_gate_count == 0
    assert result.gates == config.gates


@pytest.mark.parametrize("missing", REQUIRED_PHASE2_GATE_IDS)
def test_each_required_gate_is_required(missing: str) -> None:
    config = complete_config(gates=tuple(gate for gate in complete_config().gates if gate.gate_id != missing))
    result = evaluate_phase2_certification(config)
    assert result.overall_passed is False
    assert missing in result.missing_gate_ids


def test_failed_gate_incomplete_coverage_and_malformed_config_fail_closed() -> None:
    failed = complete_config(gates=tuple(gate.model_copy(update={"passed": False}) if gate.gate_id == "pipeline_integration" else gate for gate in complete_config().gates))
    assert evaluate_phase2_certification(failed).overall_passed is False
    assert evaluate_phase2_certification(Phase2CertificationConfig(gates=())).overall_passed is False
    with pytest.raises(ValidationError):
        Phase2CertificationConfig(schema_version="wrong", gates=())


def test_blank_evidence_and_duplicate_gate_ids_are_rejected() -> None:
    with pytest.raises(ValidationError, match="non-empty"):
        Phase2Gate(gate_id="documentation", passed=True, evidence=" ")
    gate = Phase2Gate(gate_id="documentation", passed=True, evidence="docs")
    with pytest.raises(ValueError, match="unique"):
        Phase2CertificationConfig(gates=(gate, gate))


@pytest.mark.parametrize(
    "violation",
    ["model_selection", "provider_selection", "hardware_selection", "placement_selection", "scheduler_decision", "execution_graph_or_runtime"],
)
def test_resource_selection_boundary_violations_force_fail(violation: str) -> None:
    result = evaluate_phase2_certification(complete_config(boundary_violations=(violation,)))
    assert result.overall_passed is False
    assert result.boundary_violations == (violation,)


def test_gate_and_evidence_collections_are_immutable() -> None:
    result = evaluate_phase2_certification(complete_config())
    with pytest.raises((AttributeError, TypeError, ValidationError)):
        result.gates += ()


def test_machine_readable_phase2_config_evaluates_to_pass() -> None:
    config = Phase2CertificationConfig.model_validate(json.loads(CONFIG.read_text(encoding="utf-8")))
    result = evaluate_phase2_certification(config)
    assert result.overall_passed is True
    assert tuple(gate.gate_id for gate in result.gates) == REQUIRED_PHASE2_GATE_IDS
