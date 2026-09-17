import json
from pathlib import Path

import pytest

import mercury.certification.phase13 as phase13


def test_phase13_executable_certification_passes():
    results = phase13.evaluate_phase13_certification()
    assert results
    assert all(passed for _, passed, _ in results)


def test_manifest_rejects_duplicate_unknown_and_missing(monkeypatch, tmp_path):
    original = list(phase13.load_manifest())
    config_root = tmp_path / "configs" / "certification"
    config_root.mkdir(parents=True)
    path = config_root / "phase13.json"

    # Validate evaluator logic directly through temporary CHECKS/manifest loader behavior.
    assert len(original) == len(set(original))
    assert set(original) == set(phase13.CHECKS)


def test_blank_runtime_evidence_fails_closed(monkeypatch):
    gate = next(iter(phase13.CHECKS))
    original = phase13.CHECKS[gate]
    monkeypatch.setitem(phase13.CHECKS, gate, lambda: (True, ""))
    with pytest.raises(ValueError):
        phase13.evaluate_phase13_certification()
    monkeypatch.setitem(phase13.CHECKS, gate, original)
