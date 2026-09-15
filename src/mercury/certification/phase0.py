from __future__ import annotations

from typing import Literal

from pydantic import field_validator, model_validator

from mercury.contracts.base import ContractModel


REQUIRED_PHASE0_GATE_IDS: tuple[str, ...] = (
    "context_boundary",
    "recovery_state",
    "decision_provenance",
    "prerequisite_validation",
    "trace_context",
    "runtime_events",
    "telemetry_evidence",
    "slo_evidence",
    "failure_scenarios",
    "full_regression_suite",
    "artifact_integrity",
    "documentation",
    "git_cleanliness_evidence",
)


class Phase0Gate(ContractModel):
    gate_id: str
    passed: bool
    evidence: str

    @field_validator("gate_id", "evidence")
    @classmethod
    def gate_evidence_is_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("gate evidence must be non-empty")
        return value


class Phase0CertificationConfig(ContractModel):
    schema_version: Literal["mercury.certification.phase0/v1"] = (
        "mercury.certification.phase0/v1"
    )
    gates: tuple[Phase0Gate, ...]

    @model_validator(mode="after")
    def gate_ids_are_unique(self) -> Phase0CertificationConfig:
        gate_ids = tuple(gate.gate_id for gate in self.gates)
        if len(gate_ids) != len(set(gate_ids)):
            raise ValueError("gate ids must be unique")
        return self


class Phase0CertificationResult(ContractModel):
    schema_version: Literal["mercury.certification.phase0-result/v1"] = (
        "mercury.certification.phase0-result/v1"
    )
    overall_passed: bool
    gates: tuple[Phase0Gate, ...]
    missing_gate_ids: tuple[str, ...]
    passed_gate_count: int
    failed_gate_count: int


def evaluate_phase0_certification(
    config: Phase0CertificationConfig,
) -> Phase0CertificationResult:
    gates_by_id = {gate.gate_id: gate for gate in config.gates}
    missing_gate_ids = tuple(
        gate_id for gate_id in REQUIRED_PHASE0_GATE_IDS if gate_id not in gates_by_id
    )
    required_gates = tuple(
        gates_by_id[gate_id]
        for gate_id in REQUIRED_PHASE0_GATE_IDS
        if gate_id in gates_by_id
    )
    passed_gate_count = sum(gate.passed for gate in required_gates)
    failed_gate_count = len(required_gates) - passed_gate_count
    overall_passed = not missing_gate_ids and not failed_gate_count
    return Phase0CertificationResult(
        overall_passed=overall_passed,
        gates=config.gates,
        missing_gate_ids=missing_gate_ids,
        passed_gate_count=passed_gate_count,
        failed_gate_count=failed_gate_count,
    )
