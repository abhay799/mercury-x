import json
from pathlib import Path

from mercury.certification.phase13_checks import CHECKS

PHASE13_CERTIFICATION_SCHEMA = "mercury.phase13-certification/v1"
REQUIRED_PHASE13_GATE_IDS = tuple(CHECKS)


def load_manifest(config_path: Path | None = None):
    path = config_path or Path(__file__).parents[3] / "configs" / "certification" / "phase13.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("phase13 manifest unavailable or malformed") from exc
    if not isinstance(payload, dict) or set(payload) != {"schema_version", "required_gates"} or payload.get("schema_version") != PHASE13_CERTIFICATION_SCHEMA:
        raise ValueError("invalid phase13 manifest schema")
    gates = payload.get("required_gates")
    if not isinstance(gates, list) or not gates or any(not isinstance(gate, str) or not gate.strip() for gate in gates):
        raise ValueError("phase13 certification manifest requires nonempty required_gates")
    if len(gates) != len(set(gates)):
        raise ValueError("duplicate Phase 13 certification gate")
    unknown = [gate for gate in gates if gate not in CHECKS]
    if unknown:
        raise ValueError(f"unknown Phase 13 certification gate: {unknown[0]}")
    missing = [gate for gate in CHECKS if gate not in gates]
    if missing:
        raise ValueError(f"missing Phase 13 certification gate: {missing[0]}")
    if tuple(gates) != REQUIRED_PHASE13_GATE_IDS or tuple(CHECKS) != REQUIRED_PHASE13_GATE_IDS:
        raise ValueError("phase13 check registry mismatch")
    return tuple(gates)


def evaluate_phase13_certification(config_path: Path | None = None):
    results = []
    for gate in load_manifest(config_path):
        passed, evidence = CHECKS[gate]()
        if not isinstance(evidence, str) or not evidence.strip():
            raise ValueError(f"blank certification evidence for gate {gate}")
        results.append((gate, bool(passed), evidence))
    return tuple(results)


def main():
    results = evaluate_phase13_certification()
    failures = [item for item in results if not item[1]]
    for gate, passed, evidence in results:
        print(f"{gate}: {'PASS' if passed else 'FAIL'} - {evidence}")
    print("PASS" if not failures else "FAIL")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
