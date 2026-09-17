from json import loads
from pathlib import Path
from typing import Literal

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
    schema_version: Literal["mercury.phase10-certification/v1"] = "mercury.phase10-certification/v1"
    gates: tuple[Phase10Gate, ...]

    @model_validator(mode="after")
    def valid(self):
        ids = [gate.gate_id for gate in self.gates]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate gate")
        if any(gate_id not in REQUIRED_PHASE10_GATE_IDS for gate_id in ids):
            raise ValueError("unknown gate")
        return self


class Phase10GateResult(ContractModel):
    gate_id: str
    check_id: str
    passed: bool
    reason: str
    evidence: str

    @field_validator("gate_id", "check_id", "reason", "evidence")
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError("nonblank finding required")
        return value


class Phase10CertificationResult(ContractModel):
    overall_passed: bool
    passed_gate_count: int
    failed_gate_count: int
    missing_gate_ids: tuple[str, ...]
    gate_results: tuple[Phase10GateResult, ...]


def evaluate_phase10_certification(config):
    if not isinstance(config, Phase10CertificationConfig):
        raise ValueError("config required")
    # Revalidate even frozen objects: model_copy/model_construct can bypass validation.
    config = Phase10CertificationConfig.model_validate(config.model_dump())
    from mercury.certification import phase10_checks

    by_id = {gate.gate_id: gate for gate in config.gates}
    missing = tuple(
        gate_id for gate_id in REQUIRED_PHASE10_GATE_IDS if gate_id not in by_id
    )
    findings = []
    for gate_id in REQUIRED_PHASE10_GATE_IDS:
        check_id = f"mercury.certification.phase10_checks.check_{gate_id}"
        gate = by_id.get(gate_id)
        evidence = gate.evidence if gate is not None else "required gate missing from config"
        passed = False
        if gate is None:
            reason = "Required gate is not configured."
        else:
            try:
                phase10_checks.run_check(gate_id)
                passed = gate.passed
                reason = (
                    "Executable invariant check passed."
                    if passed else "Executable check passed, but the configured gate vetoed certification."
                )
            except Exception as exc:
                # Findings contain stable error categories; stack traces, addresses, and
                # environment-dependent exception messages are deliberately excluded.
                reason = (
                    str(exc) if isinstance(exc, phase10_checks.CertificationCheckFailure)
                    else f"Executable invariant check failed ({type(exc).__name__})."
                )
        findings.append(Phase10GateResult(
            gate_id=gate_id, check_id=check_id, passed=passed,
            reason=reason, evidence=evidence,
        ))
    passed = sum(finding.passed for finding in findings)
    failed = len(findings) - passed
    return Phase10CertificationResult(
        overall_passed=not missing and not failed,
        passed_gate_count=passed,
        failed_gate_count=failed,
        missing_gate_ids=missing,
        gate_results=tuple(findings),
    )


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate config key")
        result[key] = value
    return result


def load_phase10_certification_config(path):
    try:
        payload = loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
        return Phase10CertificationConfig.model_validate(payload)
    except (OSError, ValueError, TypeError) as exc:
        raise ValueError("missing or malformed Phase 10 certification config") from exc


def main():
    path = (
        Path(__file__).parents[3]
        / "configs"
        / "certification"
        / "phase10.json"
    )
    try:
        config = load_phase10_certification_config(path)
        result = evaluate_phase10_certification(config)
    except ValueError:
        print("FAIL: missing or malformed Phase 10 certification config")
        return 1
    print("PASS" if result.overall_passed else "FAIL")
    print(f"{result.passed_gate_count} PASS / {result.failed_gate_count} FAIL")
    for finding in result.gate_results:
        print(f"{finding.gate_id}: {'PASS' if finding.passed else 'FAIL'} - {finding.reason}")
    return 0 if result.overall_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
