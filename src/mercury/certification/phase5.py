"""Machine-readable certification contracts for the Phase 5 baseline."""

from __future__ import annotations

from typing import Literal

from pydantic import field_validator, model_validator

from mercury.contracts.base import ContractModel


REQUIRED_PHASE5_GATE_IDS: tuple[str, ...] = (
    "composition_contract",
    "certified_pattern_library",
    "candidate_instantiation",
    "composition_validation",
    "bounded_generation",
    "integration_failure_hardening",
    "identity_consistency",
    "provenance_consistency",
    "handoff_capability_evidence",
    "determinism",
    "fail_closed_behavior",
    "boundary_compliance",
    "full_regression_suite",
    "documentation",
)

KNOWN_PHASE5_CERTIFICATION_VIOLATIONS: frozenset[str] = frozenset(
    {
        "malformed_upstream_state",
        "required_source_artifact_missing",
        "identity_or_provenance_drift",
        "pattern_definition_drift",
        "capability_handoff_or_evidence_defect",
        "nondeterministic_composition_output",
        "deduplication_or_provenance_loss",
        "bounded_generation_bypass",
        "invalid_independent_failure_semantics",
    }
)

KNOWN_PHASE5_BOUNDARY_VIOLATIONS: frozenset[str] = frozenset(
    {
        "ranking_or_scoring",
        "winner_selection",
        "phase3_graph_node_assignment",
        "fallback_or_preference_ordering",
        "free_form_topology_generation",
        "recursion_or_swarm_behavior",
        "hardware_or_placement",
        "scheduler_or_runtime",
        "cost_latency_quality_optimization",
        "nested_boundary_leakage",
    }
)


class Phase5Gate(ContractModel):
    gate_id: str
    passed: bool
    evidence: str

    @field_validator("gate_id", "evidence")
    @classmethod
    def gate_text_is_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("gate evidence must be non-empty")
        return value


class Phase5CertificationConfig(ContractModel):
    schema_version: Literal["mercury.certification.phase5/v1"] = (
        "mercury.certification.phase5/v1"
    )
    gates: tuple[Phase5Gate, ...]
    certification_violations: tuple[str, ...] = ()
    boundary_violations: tuple[str, ...] = ()

    @field_validator("certification_violations")
    @classmethod
    def certification_violations_are_known_unique_and_ordered(
        cls, values: tuple[str, ...]
    ) -> tuple[str, ...]:
        if len(values) != len(set(values)):
            raise ValueError("certification violations must be unique")
        if any(value not in KNOWN_PHASE5_CERTIFICATION_VIOLATIONS for value in values):
            raise ValueError("unknown Phase 5 certification violation")
        return tuple(sorted(values))

    @field_validator("boundary_violations")
    @classmethod
    def boundary_violations_are_known_unique_and_ordered(
        cls, values: tuple[str, ...]
    ) -> tuple[str, ...]:
        if len(values) != len(set(values)):
            raise ValueError("boundary violations must be unique")
        if any(value not in KNOWN_PHASE5_BOUNDARY_VIOLATIONS for value in values):
            raise ValueError("unknown Phase 5 boundary violation")
        return tuple(sorted(values))

    @model_validator(mode="after")
    def gates_are_unique_known_and_ordered(self) -> Phase5CertificationConfig:
        gate_ids = tuple(gate.gate_id for gate in self.gates)
        if len(gate_ids) != len(set(gate_ids)):
            raise ValueError("gate ids must be unique")
        if any(gate_id not in REQUIRED_PHASE5_GATE_IDS for gate_id in gate_ids):
            raise ValueError("unknown Phase 5 certification gate")
        gates_by_id = {gate.gate_id: gate for gate in self.gates}
        object.__setattr__(
            self,
            "gates",
            tuple(
                gates_by_id[gate_id]
                for gate_id in REQUIRED_PHASE5_GATE_IDS
                if gate_id in gates_by_id
            ),
        )
        return self


class Phase5CertificationResult(ContractModel):
    schema_version: Literal["mercury.certification.phase5-result/v1"] = (
        "mercury.certification.phase5-result/v1"
    )
    overall_passed: bool
    gates: tuple[Phase5Gate, ...]
    missing_gate_ids: tuple[str, ...]
    certification_violations: tuple[str, ...]
    boundary_violations: tuple[str, ...]
    passed_gate_count: int
    failed_gate_count: int


def evaluate_phase5_certification(
    config: Phase5CertificationConfig,
) -> Phase5CertificationResult:
    """Evaluate complete bounded logical-composition certification fail closed."""
    if not isinstance(config, Phase5CertificationConfig):
        raise ValueError("config must be a Phase5CertificationConfig")
    gates_by_id = {gate.gate_id: gate for gate in config.gates}
    missing_gate_ids = tuple(
        gate_id for gate_id in REQUIRED_PHASE5_GATE_IDS if gate_id not in gates_by_id
    )
    required_gates = tuple(
        gates_by_id[gate_id]
        for gate_id in REQUIRED_PHASE5_GATE_IDS
        if gate_id in gates_by_id
    )
    passed_gate_count = sum(gate.passed for gate in required_gates)
    failed_gate_count = len(required_gates) - passed_gate_count
    overall_passed = (
        not missing_gate_ids
        and not failed_gate_count
        and not config.certification_violations
        and not config.boundary_violations
    )
    return Phase5CertificationResult(
        overall_passed=overall_passed,
        gates=config.gates,
        missing_gate_ids=missing_gate_ids,
        certification_violations=config.certification_violations,
        boundary_violations=config.boundary_violations,
        passed_gate_count=passed_gate_count,
        failed_gate_count=failed_gate_count,
    )
