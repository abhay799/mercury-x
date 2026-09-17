from json import loads
from pathlib import Path

from pydantic import field_validator, model_validator

from mercury.contracts.base import ContractModel


REQUIRED_PHASE12_GATE_IDS = ('segment_types', 'execution_states', 'handoff_kinds', 'handoff_states', 'limits', 'segment_identity', 'handoff_identity', 'plan_identity', 'plan_fingerprint', 'acyclic_graph', 'self_dependency', 'dangling_dependency', 'duplicate_segment', 'entry_terminal_detection', 'namespace_authorization', 'namespace_isolation', 'closed_namespace', 'handoff_endpoints', 'handoff_transitions', 'readiness_dependencies', 'readiness_handoffs', 'execution_transitions', 'cancellation_terminal', 'retry_limit', 'retry_eligibility', 'failure_classification', 'kv_compatibility', 'stale_invalidated_kv', 'prediction_hint_only', 'source_immutability', 'verification_before_success', 'result_stitching', 'missing_terminal_result', 'result_lineage', 'no_model_selection', 'no_precision_selection', 'no_hardware_placement', 'no_global_scheduling', 'no_migration', 'no_user_profile_prediction', 'adversarial_integration')


class Phase12Gate(ContractModel):
    gate_id: str
    passed: bool
    evidence: str

    @field_validator("gate_id", "evidence")
    @classmethod
    def text(cls, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("nonblank gate text required")
        return value


class Phase12CertificationConfig(ContractModel):
    gates: tuple[Phase12Gate, ...]

    @model_validator(mode="after")
    def valid(self):
        ids = [gate.gate_id for gate in self.gates]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate gate")
        if any(gate_id not in REQUIRED_PHASE12_GATE_IDS for gate_id in ids):
            raise ValueError("unknown gate")
        return self


class Phase12CertificationResult(ContractModel):
    overall_passed: bool
    passed_gate_count: int
    failed_gate_count: int
    missing_gate_ids: tuple[str, ...]


def evaluate_phase12_certification(config):
    if not isinstance(config, Phase12CertificationConfig):
        raise ValueError("config required")
    by_id = {gate.gate_id: gate for gate in config.gates}
    missing = tuple(
        gate_id for gate_id in REQUIRED_PHASE12_GATE_IDS if gate_id not in by_id
    )
    failed = sum(not gate.passed for gate in config.gates)
    passed = sum(gate.passed for gate in config.gates)
    return Phase12CertificationResult(
        overall_passed=not missing and not failed,
        passed_gate_count=passed,
        failed_gate_count=failed,
        missing_gate_ids=missing,
    )


def main():
    path = (
        Path(__file__).parents[3]
        / "configs"
        / "certification"
        / "phase12.json"
    )
    config = Phase12CertificationConfig(**loads(path.read_text(encoding="utf-8")))
    result = evaluate_phase12_certification(config)
    print("PASS" if result.overall_passed else "FAIL")
    return 0 if result.overall_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
