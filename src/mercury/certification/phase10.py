from json import loads
from pathlib import Path

from pydantic import field_validator, model_validator

from mercury.contracts.base import ContractModel


REQUIRED_PHASE10_GATE_IDS = ('horizons', 'confidence_bands', 'limits', 'candidate_identity', 'prediction_identity', 'namespace_authorization', 'namespace_isolation', 'closed_namespace', 'lifecycle_eligibility', 'source_traceability', 'source_immutability', 'deterministic_features', 'bounded_confidence', 'deterministic_confidence_band', 'deterministic_horizon', 'reason_codes', 'conflict_preservation', 'prediction_ordering', 'prediction_limit', 'source_limit', 'no_semantic_ranking', 'no_memory_persistence', 'no_prefetch_cache', 'no_execution_control', 'no_user_profile_prediction', 'adversarial_integration')


class Phase10Gate(ContractModel):
    gate_id: str
    passed: bool
    evidence: str

    @field_validator("gate_id", "evidence")
    @classmethod
    def text(cls, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("nonblank gate text required")
        return value


class Phase10CertificationConfig(ContractModel):
    gates: tuple[Phase10Gate, ...]

    @model_validator(mode="after")
    def valid(self):
        ids = [gate.gate_id for gate in self.gates]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate gate")
        if any(gate_id not in REQUIRED_PHASE10_GATE_IDS for gate_id in ids):
            raise ValueError("unknown gate")
        return self


class Phase10CertificationResult(ContractModel):
    overall_passed: bool
    passed_gate_count: int
    failed_gate_count: int
    missing_gate_ids: tuple[str, ...]


def evaluate_phase10_certification(config):
    if not isinstance(config, Phase10CertificationConfig):
        raise ValueError("config required")
    by_id = {gate.gate_id: gate for gate in config.gates}
    missing = tuple(
        gate_id for gate_id in REQUIRED_PHASE10_GATE_IDS if gate_id not in by_id
    )
    failed = sum(not gate.passed for gate in config.gates)
    passed = sum(gate.passed for gate in config.gates)
    return Phase10CertificationResult(
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
        / "phase10.json"
    )
    config = Phase10CertificationConfig(**loads(path.read_text(encoding="utf-8")))
    result = evaluate_phase10_certification(config)
    print("PASS" if result.overall_passed else "FAIL")
    return 0 if result.overall_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
