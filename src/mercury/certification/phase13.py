import json
from pathlib import Path

from mercury.certification.phase13_checks import CHECKS


def load_manifest():
    path = Path(__file__).parents[3] / "configs" / "certification" / "phase13.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    gates = payload.get("required_gates")
    if not isinstance(gates, list) or not gates:
        raise ValueError("phase13 certification manifest requires nonempty required_gates")
    if len(gates) != len(set(gates)):
        raise ValueError("duplicate Phase 13 certification gate")
    unknown = [gate for gate in gates if gate not in CHECKS]
    if unknown:
        raise ValueError(f"unknown Phase 13 certification gate: {unknown[0]}")
    missing = [gate for gate in CHECKS if gate not in gates]
    if missing:
        raise ValueError(f"missing Phase 13 certification gate: {missing[0]}")
    return tuple(gates)


def evaluate_phase13_certification():
    results = []
    for gate in load_manifest():
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
