"""Fail-closed executable certification for Phase 15 placement prediction."""

import json
from pathlib import Path

from mercury.certification.phase15_checks import CHECKS


PHASE15_CERTIFICATION_SCHEMA = "mercury.phase15-certification/v1"
REQUIRED_PHASE15_GATE_IDS = (
    "contracts",
    "determinism",
    "uncalibrated",
    "eligibility",
    "no_execution",
)


def load_manifest(config_path: Path | None = None) -> tuple[str, ...]:
    path = config_path or Path(__file__).parents[3] / "configs" / "certification" / "phase15.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("phase15 manifest unavailable or malformed") from exc
    if (
        not isinstance(payload, dict)
        or payload.get("schema_version") != PHASE15_CERTIFICATION_SCHEMA
        or set(payload) != {"schema_version", "required_gates"}
    ):
        raise ValueError("invalid phase15 manifest")
    gates = payload.get("required_gates")
    if (
        not isinstance(gates, list)
        or any(not isinstance(gate, str) for gate in gates)
        or len(gates) != len(set(gates))
        or tuple(gates) != REQUIRED_PHASE15_GATE_IDS
        or tuple(CHECKS) != REQUIRED_PHASE15_GATE_IDS
    ):
        raise ValueError("invalid phase15 manifest")
    return tuple(gates)


def evaluate(config_path: Path | None = None):
    results = []
    for gate in load_manifest(config_path):
        passed, evidence = CHECKS[gate]()
        if not isinstance(evidence, str) or not evidence.strip():
            raise ValueError(f"blank certification evidence for gate {gate}")
        results.append((gate, bool(passed), evidence))
    return tuple(results)


def main():
    results = evaluate()
    failures = [result for result in results if not result[1]]
    for gate, passed, evidence in results:
        print(f"{gate}: {'PASS' if passed else 'FAIL'} - {evidence}")
    print("PASS" if not failures else "FAIL")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
