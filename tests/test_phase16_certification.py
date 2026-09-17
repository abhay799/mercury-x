import json
import pytest

from mercury.certification import phase16


def test_phase16_certification():
    assert all(x[1] for x in phase16.evaluate())


def test_phase16_certification_does_not_hardcode_gate_success(monkeypatch) -> None:
    monkeypatch.setitem(phase16.CHECKS, "states", lambda: (False, "forced failure"))

    assert not all(result[1] for result in phase16.evaluate())


@pytest.mark.parametrize("mutation", ["missing", "unknown", "duplicate", "blank", "extra", "schema"])
def test_phase16_manifest_fails_closed_for_invalid_configuration(tmp_path, mutation):
    gates = list(phase16.REQUIRED_PHASE16_GATE_IDS)
    payload = {"schema_version": phase16.PHASE16_CERTIFICATION_SCHEMA, "required_gates": gates}
    if mutation == "missing": payload["required_gates"] = gates[:-1]
    elif mutation == "unknown": payload["required_gates"][-1] = "unknown"
    elif mutation == "duplicate": payload["required_gates"][-1] = gates[0]
    elif mutation == "blank": payload["required_gates"][-1] = " "
    elif mutation == "extra": payload["extra"] = True
    elif mutation == "schema": payload["schema_version"] = "unsupported"
    path = tmp_path / "phase16.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError):
        phase16.evaluate(path)


def test_phase16_manifest_rejects_missing_and_malformed_files(tmp_path):
    with pytest.raises(ValueError): phase16.evaluate(tmp_path / "missing.json")
    bad = tmp_path / "bad.json"; bad.write_text("{", encoding="utf-8")
    with pytest.raises(ValueError): phase16.evaluate(bad)


def test_phase16_manifest_rejects_check_registry_mismatch(monkeypatch):
    monkeypatch.setitem(phase16.CHECKS, "unexpected", lambda: (True, "unexpected"))
    with pytest.raises(ValueError):
        phase16.evaluate()
