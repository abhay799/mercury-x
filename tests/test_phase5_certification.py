from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from mercury.certification.phase5 import (
    KNOWN_PHASE5_BOUNDARY_VIOLATIONS,
    KNOWN_PHASE5_CERTIFICATION_VIOLATIONS,
    REQUIRED_PHASE5_GATE_IDS,
    Phase5CertificationConfig,
    Phase5Gate,
    evaluate_phase5_certification,
)


CONFIG = Path("configs/certification/phase5.json")


def complete_config(**changes: object) -> Phase5CertificationConfig:
    values: dict[str, object] = {
        "gates": tuple(
            Phase5Gate(
                gate_id=gate_id,
                passed=True,
                evidence=f"deterministic evidence for {gate_id}",
            )
            for gate_id in REQUIRED_PHASE5_GATE_IDS
        ),
        "certification_violations": (),
        "boundary_violations": (),
    }
    values.update(changes)
    return Phase5CertificationConfig(**values)


def test_complete_phase5_certification_requires_all_14_gates() -> None:
    config = complete_config()

    result = evaluate_phase5_certification(config)

    assert result.overall_passed is True
    assert (result.passed_gate_count, result.failed_gate_count) == (14, 0)
    assert tuple(gate.gate_id for gate in result.gates) == REQUIRED_PHASE5_GATE_IDS
    assert result == evaluate_phase5_certification(config)


@pytest.mark.parametrize("missing", REQUIRED_PHASE5_GATE_IDS)
def test_every_required_phase5_gate_fails_closed_when_missing(missing: str) -> None:
    gates = tuple(gate for gate in complete_config().gates if gate.gate_id != missing)

    result = evaluate_phase5_certification(complete_config(gates=gates))

    assert result.overall_passed is False
    assert result.missing_gate_ids == (missing,)


def test_failed_gate_and_incomplete_coverage_fail_closed() -> None:
    failed_gates = tuple(
        gate.model_copy(update={"passed": False})
        if gate.gate_id == "composition_validation"
        else gate
        for gate in complete_config().gates
    )

    failed = evaluate_phase5_certification(complete_config(gates=failed_gates))
    incomplete = evaluate_phase5_certification(Phase5CertificationConfig(gates=()))

    assert failed.overall_passed is False
    assert (failed.passed_gate_count, failed.failed_gate_count) == (13, 1)
    assert incomplete.overall_passed is False
    assert incomplete.missing_gate_ids == REQUIRED_PHASE5_GATE_IDS


def test_blank_duplicate_unknown_and_malformed_config_are_rejected() -> None:
    with pytest.raises(ValidationError, match="non-empty"):
        Phase5Gate(gate_id="documentation", passed=True, evidence=" ")
    duplicate = Phase5Gate(gate_id="documentation", passed=True, evidence="docs")
    with pytest.raises(ValueError, match="unique"):
        Phase5CertificationConfig(gates=(duplicate, duplicate))
    with pytest.raises(ValueError, match="unknown"):
        Phase5CertificationConfig(
            gates=(Phase5Gate(gate_id="unknown", passed=True, evidence="invalid"),)
        )
    with pytest.raises(ValidationError):
        Phase5CertificationConfig(schema_version="mercury.certification.phase5/v2", gates=())


@pytest.mark.parametrize("violation", sorted(KNOWN_PHASE5_CERTIFICATION_VIOLATIONS))
def test_known_phase5_lifecycle_violations_force_fail(violation: str) -> None:
    result = evaluate_phase5_certification(
        complete_config(certification_violations=(violation,))
    )

    assert result.overall_passed is False
    assert result.certification_violations == (violation,)


@pytest.mark.parametrize("violation", sorted(KNOWN_PHASE5_BOUNDARY_VIOLATIONS))
def test_known_phase5_boundary_violations_including_nested_leakage_force_fail(
    violation: str,
) -> None:
    result = evaluate_phase5_certification(
        complete_config(boundary_violations=(violation,))
    )

    assert result.overall_passed is False
    assert result.boundary_violations == (violation,)


def test_violation_vocabularies_are_closed_unique_and_canonical() -> None:
    with pytest.raises(ValueError, match="unique"):
        complete_config(
            certification_violations=(
                "malformed_upstream_state",
                "malformed_upstream_state",
            )
        )
    with pytest.raises(ValueError, match="unknown"):
        complete_config(boundary_violations=("unknown_phase6_leakage",))

    config = complete_config(
        certification_violations=(
            "pattern_definition_drift",
            "malformed_upstream_state",
        ),
        boundary_violations=(
            "nested_boundary_leakage",
            "winner_selection",
        ),
    )

    assert config.certification_violations == (
        "malformed_upstream_state",
        "pattern_definition_drift",
    )
    assert config.boundary_violations == (
        "nested_boundary_leakage",
        "winner_selection",
    )


def test_gate_result_and_evidence_collections_are_immutable() -> None:
    config = complete_config()
    result = evaluate_phase5_certification(config)

    with pytest.raises((AttributeError, TypeError, ValidationError)):
        result.gates += ()
    with pytest.raises((AttributeError, TypeError, ValidationError)):
        config.gates[0].evidence = "changed"


def test_machine_readable_phase5_config_passes_with_full_canonical_coverage() -> None:
    config = Phase5CertificationConfig.model_validate(
        json.loads(CONFIG.read_text(encoding="utf-8"))
    )

    result = evaluate_phase5_certification(config)

    assert result.overall_passed is True
    assert tuple(gate.gate_id for gate in result.gates) == REQUIRED_PHASE5_GATE_IDS
    assert (result.passed_gate_count, result.failed_gate_count) == (14, 0)
    assert result.certification_violations == ()
    assert result.boundary_violations == ()
