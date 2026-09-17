import json
import pytest

from mercury.certification.phase14 import evaluate


EXPECTED_GATES = {
    "exact_enums",
    "graph_identity",
    "node_link_integrity",
    "locality",
    "directed_paths",
    "asymmetric_links",
    "disconnected_graphs",
    "cyclic_graphs",
    "multihop_paths",
    "deterministic_path_selection",
    "metrics_unknown",
    "declared_measured_metrics",
    "path_provenance",
    "path_result_contract",
    "path_refresh",
    "phase13_integration",
    "graph_generation",
    "permutation_invariance",
    "malformed_contract_rejection",
    "no_placement",
    "no_scheduler",
}


def test_phase14_certification_has_a_distinct_behavioral_gate_for_every_invariant():
    results = evaluate()
    assert {gate for gate, _, _ in results} == EXPECTED_GATES
    assert all(ok for _, ok, _ in results)
    assert all(evidence.strip() for _, _, evidence in results)


@pytest.mark.parametrize("mutation", ["missing", "unknown", "duplicate", "blank", "extra", "schema"])
def test_phase14_certification_fails_closed_for_invalid_manifest(tmp_path, mutation):
    from mercury.certification import phase14
    gates = list(phase14.REQUIRED_PHASE14_GATE_IDS)
    payload = {"schema_version": phase14.PHASE14_CERTIFICATION_SCHEMA, "required_gates": gates}
    if mutation == "missing": payload["required_gates"] = gates[:-1]
    elif mutation == "unknown": payload["required_gates"][-1] = "unknown"
    elif mutation == "duplicate": payload["required_gates"][-1] = gates[0]
    elif mutation == "blank": payload["required_gates"][-1] = " "
    elif mutation == "extra": payload["extra"] = True
    elif mutation == "schema": payload["schema_version"] = "unsupported"
    path = tmp_path / "phase14.json"; path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError): phase14.evaluate(path)


def test_phase14_manifest_missing_malformed_and_registry_mismatch_fail_closed(monkeypatch, tmp_path):
    from mercury.certification import phase14
    with pytest.raises(ValueError): phase14.evaluate(tmp_path / "missing.json")
    bad = tmp_path / "bad.json"; bad.write_text("{", encoding="utf-8")
    with pytest.raises(ValueError): phase14.evaluate(bad)
    monkeypatch.setitem(phase14.CHECKS, "unexpected", lambda: (True, "unexpected"))
    with pytest.raises(ValueError): phase14.evaluate()
