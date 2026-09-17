import pytest

from mercury.context_prediction import candidates, scoring

from mercury.certification.phase10 import (
    REQUIRED_PHASE10_GATE_IDS,
    Phase10CertificationConfig,
    Phase10Gate,
    evaluate_phase10_certification,
)


def complete():
    return Phase10CertificationConfig(
        gates=tuple(
            Phase10Gate(gate_id=gate_id, passed=True, evidence="verified")
            for gate_id in REQUIRED_PHASE10_GATE_IDS
        )
    )


def test_complete_config_passes():
    result = evaluate_phase10_certification(complete())
    assert result.overall_passed
    assert result.failed_gate_count == 0
    assert result.missing_gate_ids == ()


def test_missing_gate_fails_closed():
    result = evaluate_phase10_certification(
        Phase10CertificationConfig(gates=complete().gates[:-1])
    )
    assert not result.overall_passed


def test_failed_gate_fails_closed():
    gates = list(complete().gates)
    gates[0] = Phase10Gate(
        gate_id=gates[0].gate_id,
        passed=False,
        evidence="failed",
    )
    assert not evaluate_phase10_certification(
        Phase10CertificationConfig(gates=tuple(gates))
    ).overall_passed


def test_unknown_duplicate_blank_and_nonconfig_fail_closed():
    with pytest.raises(Exception):
        Phase10CertificationConfig(
            gates=(Phase10Gate(gate_id="unknown", passed=True, evidence="x"),)
        )
    gate = Phase10Gate(
        gate_id=REQUIRED_PHASE10_GATE_IDS[0],
        passed=True,
        evidence="x",
    )
    with pytest.raises(Exception):
        Phase10CertificationConfig(gates=(gate, gate))
    with pytest.raises(Exception):
        Phase10Gate(
            gate_id=REQUIRED_PHASE10_GATE_IDS[0],
            passed=True,
            evidence="",
        )
    with pytest.raises(ValueError):
        evaluate_phase10_certification({"gates": []})


def test_all_true_flags_cannot_certify_broken_scoring(monkeypatch):
    original = scoring.score_prediction

    def broken(features):
        horizon, confidence, band, reasons = original(features)
        return horizon, 2.0, band, reasons

    monkeypatch.setattr(scoring, "score_prediction", broken)
    result = evaluate_phase10_certification(complete())
    assert not result.overall_passed
    assert "bounded_confidence" in tuple(
        finding.gate_id for finding in result.gate_results if not finding.passed
    )


def test_all_true_flags_cannot_certify_ignored_namespace_closure(monkeypatch):
    monkeypatch.setattr(candidates, "build_prediction_candidates", lambda *a, **k: ())
    result = evaluate_phase10_certification(complete())
    assert not result.overall_passed
    assert "closed_namespace" in tuple(
        finding.gate_id for finding in result.gate_results if not finding.passed
    )


def test_each_gate_has_deterministic_executable_evidence_and_frozen_findings():
    first = evaluate_phase10_certification(complete())
    second = evaluate_phase10_certification(
        Phase10CertificationConfig(gates=tuple(reversed(complete().gates)))
    )
    assert first == second
    assert tuple(item.gate_id for item in first.gate_results) == REQUIRED_PHASE10_GATE_IDS
    assert all(item.check_id and item.reason and item.evidence for item in first.gate_results)
    assert first.passed_gate_count + first.failed_gate_count == 26
    with pytest.raises(Exception):
        first.gate_results[0].passed = False
    with pytest.raises(TypeError):
        first.gate_results[0] = first.gate_results[1]


@pytest.mark.parametrize("content", ["{", "{}", '{"schema_version":"unsupported","gates":[]}'])
def test_loader_rejects_malformed_or_unsupported_config(tmp_path, content):
    from mercury.certification.phase10 import load_phase10_certification_config

    path = tmp_path / "config.json"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError):
        load_phase10_certification_config(path)


def test_loader_rejects_missing_config(tmp_path):
    from mercury.certification.phase10 import load_phase10_certification_config

    with pytest.raises(ValueError):
        load_phase10_certification_config(tmp_path / "missing.json")


def test_missing_check_artifact_cannot_pass(monkeypatch):
    from mercury.certification import phase10

    original = phase10.Path.is_file
    monkeypatch.setattr(
        phase10.Path, "is_file",
        lambda path: False if path.name == "scoring.py" else original(path),
    )
    result = evaluate_phase10_certification(complete())
    assert not result.overall_passed
    assert result.failed_gate_count > 0


def test_loader_rejects_duplicate_json_keys(tmp_path):
    from mercury.certification.phase10 import load_phase10_certification_config

    path = tmp_path / "config.json"
    path.write_text('{"gates":[],"gates":[]}', encoding="utf-8")
    with pytest.raises(ValueError):
        load_phase10_certification_config(path)
