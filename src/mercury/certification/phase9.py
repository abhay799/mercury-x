from json import loads
from pathlib import Path

from pydantic import field_validator, model_validator

from mercury.contracts.base import ContractModel


REQUIRED_PHASE9_GATE_IDS = (
    "memory_types",
    "namespaces",
    "lifecycle",
    "conflict_states",
    "statuses",
    "store_limit",
    "retrieval_limit",
    "promotion_limit",
    "consolidation_limit",
    "deterministic_identity",
    "explicit_promotion",
    "namespace_authorization",
    "namespace_isolation",
    "secret_rejection",
    "immutable_versioning",
    "conflict_preservation",
    "deterministic_retrieval",
    "governance",
    "forbidden_global_scope",
    "no_semantic_ranking",
    "no_execution_control",
    "adversarial_integration",
)


class Phase9Gate(ContractModel):
    gate_id: str
    passed: bool
    evidence: str

    @field_validator("gate_id", "evidence")
    @classmethod
    def text(cls, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("nonblank gate text required")
        return value


class Phase9CertificationConfig(ContractModel):
    gates: tuple[Phase9Gate, ...]

    @model_validator(mode="after")
    def valid(self):
        ids = [gate.gate_id for gate in self.gates]

        if len(ids) != len(set(ids)):
            raise ValueError("duplicate gate")

        if any(
            gate_id not in REQUIRED_PHASE9_GATE_IDS
            for gate_id in ids
        ):
            raise ValueError("unknown gate")

        return self


class Phase9CertificationResult(ContractModel):
    overall_passed: bool
    passed_gate_count: int
    failed_gate_count: int
    missing_gate_ids: tuple[str, ...]


def evaluate_phase9_certification(
    config: Phase9CertificationConfig,
) -> Phase9CertificationResult:
    if not isinstance(
        config,
        Phase9CertificationConfig,
    ):
        raise ValueError("config required")

    by_id = {
        gate.gate_id: gate
        for gate in config.gates
    }

    missing = tuple(
        gate_id
        for gate_id in REQUIRED_PHASE9_GATE_IDS
        if gate_id not in by_id
    )

    failed = sum(
        not gate.passed
        for gate in config.gates
    )

    passed = sum(
        gate.passed
        for gate in config.gates
    )

    return Phase9CertificationResult(
        overall_passed=not missing and not failed,
        passed_gate_count=passed,
        failed_gate_count=failed,
        missing_gate_ids=missing,
    )


def main():
    config_path = (
        Path(__file__).parents[3]
        / "configs"
        / "certification"
        / "phase9.json"
    )

    config = Phase9CertificationConfig(
        **loads(
            config_path.read_text(
                encoding="utf-8"
            )
        )
    )

    result = evaluate_phase9_certification(
        config
    )

    print(
        "PASS"
        if result.overall_passed
        else "FAIL"
    )

    return 0 if result.overall_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())