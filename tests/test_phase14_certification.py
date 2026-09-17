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


def test_phase14_certification_fails_closed_for_missing_or_unknown_gate(tmp_path):
    from mercury.certification.phase14 import evaluate
    bad_manifest = tmp_path / "phase14.json"
    bad_manifest.write_text('{"required_gates": ["directed_paths", "unknown"]}')
    with pytest.raises(ValueError, match="invalid phase14 manifest"):
        evaluate(config_path=bad_manifest)
