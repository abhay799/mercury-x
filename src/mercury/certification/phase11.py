from json import loads
from pathlib import Path

from pydantic import field_validator, model_validator

from mercury.contracts.base import ContractModel


REQUIRED_PHASE11_GATE_IDS = ('reuse_modes', 'cache_states', 'limits', 'semantic_identity', 'cache_entry_identity', 'metadata_size', 'namespace_authorization', 'namespace_isolation', 'closed_namespace', 'source_lineage', 'exact_compatibility', 'semantic_compatibility', 'physical_kv_compatibility', 'model_identity', 'model_version', 'tokenizer_identity', 'precision', 'attention_layout', 'kv_format', 'context_generation', 'payload_reference', 'payload_fingerprint', 'store_capacity', 'lookup_limit', 'source_limit', 'dependency_limit', 'lookup_ordering', 'stale_exclusion', 'invalidated_exclusion', 'deterministic_invalidation', 'dependency_invalidation', 'prediction_hint_only', 'no_semantic_only_physical_reuse', 'no_model_selection', 'no_precision_conversion', 'no_hardware_placement', 'no_scheduler_runtime', 'no_user_profile_prediction', 'adversarial_integration')


class Phase11Gate(ContractModel):
    gate_id: str
    passed: bool
    evidence: str

    @field_validator("gate_id", "evidence")
    @classmethod
    def text(cls, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("nonblank gate text required")
        return value


class Phase11CertificationConfig(ContractModel):
    gates: tuple[Phase11Gate, ...]

    @model_validator(mode="after")
    def valid(self):
        ids = [gate.gate_id for gate in self.gates]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate gate")
        if any(gate_id not in REQUIRED_PHASE11_GATE_IDS for gate_id in ids):
            raise ValueError("unknown gate")
        return self


class Phase11CertificationResult(ContractModel):
    overall_passed: bool
    passed_gate_count: int
    failed_gate_count: int
    missing_gate_ids: tuple[str, ...]


def evaluate_phase11_certification(config):
    if not isinstance(config, Phase11CertificationConfig):
        raise ValueError("config required")
    by_id = {gate.gate_id: gate for gate in config.gates}
    missing = tuple(
        gate_id for gate_id in REQUIRED_PHASE11_GATE_IDS if gate_id not in by_id
    )
    failed = sum(not gate.passed for gate in config.gates)
    passed = sum(gate.passed for gate in config.gates)
    return Phase11CertificationResult(
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
        / "phase11.json"
    )
    config = Phase11CertificationConfig(**loads(path.read_text(encoding="utf-8")))
    result = evaluate_phase11_certification(config)
    print("PASS" if result.overall_passed else "FAIL")
    return 0 if result.overall_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
