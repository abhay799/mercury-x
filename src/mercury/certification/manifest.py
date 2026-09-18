import json
from pathlib import Path


def load_certification_manifest(path: Path, *, phase: int, known_gates) -> tuple[str, ...]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid phase{phase} manifest") from exc
    if not isinstance(document, dict) or set(document) != {"schema_version", "phase", "required_gates"}:
        raise ValueError(f"invalid phase{phase} manifest")
    if document["schema_version"] != "mercury.certification/v1" or document["phase"] != phase:
        raise ValueError(f"invalid phase{phase} manifest schema")
    gates = document["required_gates"]
    if not isinstance(gates, list) or not gates or any(not isinstance(g, str) or not g.strip() for g in gates):
        raise ValueError(f"invalid phase{phase} gates")
    if len(gates) != len(set(gates)) or set(gates) != set(known_gates):
        raise ValueError(f"invalid phase{phase} manifest")
    return tuple(gates)
