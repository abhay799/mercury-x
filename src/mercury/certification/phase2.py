"""Machine-readable certification contracts for the Phase 2 baseline."""

from __future__ import annotations

from typing import Literal

from pydantic import field_validator, model_validator

from mercury.contracts.base import ContractModel


REQUIRED_PHASE2_GATE_IDS: tuple[str, ...] = (
    "workload_intelligence_contract",
    "signal_extraction",
    "intelligence_inference",
    "confidence_evidence_calibration",
    "pipeline_integration",
    "failure_edge_cases",
    "identity_consistency",
    "determinism",
    "evidence_provenance",
    "fail_closed_behavior",
    "boundary_compliance",
    "full_regression_suite",
    "documentation",
)

KNOWN_PHASE2_BOUNDARY_VIOLATIONS: frozenset[str] = frozenset(
    {
        "model_selection",
        "provider_selection",
        "model_family_selection",
        "hardware_selection",
        "placement_selection",
        "scheduler_decision",
        "execution_graph_or_runtime",
        "migration",
        "speculative_execution",
        "autonomous_optimization",
    }
)


class Phase2Gate(ContractModel):
    gate_id: str
    passed: bool
    evidence: str

    @field_validator("gate_id", "evidence")
    @classmethod
    def gate_evidence_is_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("gate evidence must be non-empty")
        return value


class Phase2CertificationConfig(ContractModel):
    schema_version: Literal["mercury.certification.phase2/v1"] = (
        "mercury.certification.phase2/v1"
    )
    gates: tuple[Phase2Gate, ...]
    boundary_violations: tuple[str, ...] = ()

    @field_validator("boundary_violations")
    @classmethod
    def boundary_violations_are_known_and_unique(
        cls, values: tuple[str, ...]
    ) -> tuple[str, ...]:
        if len(values) != len(set(values)):
            raise ValueError("boundary violations must be unique")
        if any(value not in KNOWN_PHASE2_BOUNDARY_VIOLATIONS for value in values):
            raise ValueError("unknown Phase 2 boundary violation")
        return values

    @model_validator(mode="after")
    def gate_ids_are_unique(self) -> Phase2CertificationConfig:
        gate_ids = tuple(gate.gate_id for gate in self.gates)
        if len(gate_ids) != len(set(gate_ids)):
            raise ValueError("gate ids must be unique")
        return self


class Phase2CertificationResult(ContractModel):
    schema_version: Literal["mercury.certification.phase2-result/v1"] = (
        "mercury.certification.phase2-result/v1"
    )
    overall_passed: bool
    gates: tuple[Phase2Gate, ...]
    missing_gate_ids: tuple[str, ...]
    boundary_violations: tuple[str, ...]
    passed_gate_count: int
    failed_gate_count: int


def evaluate_phase2_certification(
    config: Phase2CertificationConfig,
) -> Phase2CertificationResult:
    """Evaluate required Phase 2 gate coverage without resource selection."""
    gates_by_id = {gate.gate_id: gate for gate in config.gates}
    missing_gate_ids = tuple(
        gate_id for gate_id in REQUIRED_PHASE2_GATE_IDS if gate_id not in gates_by_id
    )
    required_gates = tuple(
        gates_by_id[gate_id]
        for gate_id in REQUIRED_PHASE2_GATE_IDS
        if gate_id in gates_by_id
    )
    passed_gate_count = sum(gate.passed for gate in required_gates)
    failed_gate_count = len(required_gates) - passed_gate_count
    overall_passed = (
        not missing_gate_ids
        and not failed_gate_count
        and not config.boundary_violations
    )
    return Phase2CertificationResult(
        overall_passed=overall_passed,
        gates=config.gates,
        missing_gate_ids=missing_gate_ids,
        boundary_violations=config.boundary_violations,
        passed_gate_count=passed_gate_count,
        failed_gate_count=failed_gate_count,
    )
