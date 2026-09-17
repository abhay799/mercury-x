import json
from pathlib import Path

import pytest

import mercury.certification.phase13 as phase13


def test_phase13_executable_certification_passes():
    results = phase13.evaluate_phase13_certification()
    assert results
    assert all(passed for _, passed, _ in results)


@pytest.mark.parametrize("mutation", ["missing", "unknown", "duplicate", "blank", "extra", "schema"])
def test_manifest_rejects_duplicate_unknown_missing_blank_extra_and_schema(tmp_path, mutation):
    gates = list(phase13.REQUIRED_PHASE13_GATE_IDS)
    payload = {"schema_version": phase13.PHASE13_CERTIFICATION_SCHEMA, "required_gates": gates}
    if mutation == "missing": payload["required_gates"] = gates[:-1]
    elif mutation == "unknown": payload["required_gates"][-1] = "unknown"
    elif mutation == "duplicate": payload["required_gates"][-1] = gates[0]
    elif mutation == "blank": payload["required_gates"][-1] = " "
    elif mutation == "extra": payload["extra"] = True
    elif mutation == "schema": payload["schema_version"] = "unsupported"
    path = tmp_path / "phase13.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError):
        phase13.load_manifest(path)


def test_phase13_manifest_missing_malformed_and_registry_mismatch_fail_closed(monkeypatch, tmp_path):
    with pytest.raises(ValueError): phase13.load_manifest(tmp_path / "missing.json")
    malformed = tmp_path / "bad.json"; malformed.write_text("{", encoding="utf-8")
    with pytest.raises(ValueError): phase13.load_manifest(malformed)
    monkeypatch.setitem(phase13.CHECKS, "unexpected", lambda: (True, "bad"))
    with pytest.raises(ValueError):
        phase13.load_manifest()


def test_blank_runtime_evidence_fails_closed(monkeypatch):
    gate = next(iter(phase13.CHECKS))
    original = phase13.CHECKS[gate]
    monkeypatch.setitem(phase13.CHECKS, gate, lambda: (True, ""))
    with pytest.raises(ValueError):
        phase13.evaluate_phase13_certification()
    monkeypatch.setitem(phase13.CHECKS, gate, original)
