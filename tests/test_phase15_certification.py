import json

import pytest

from mercury.certification.phase15 import REQUIRED_PHASE15_GATE_IDS, evaluate


def test_phase15_certification_runs_each_required_behavioral_gate():
    results = evaluate()
    assert tuple(gate for gate, _, _ in results) == REQUIRED_PHASE15_GATE_IDS
    assert all(passed for _, passed, _ in results)
    assert len({id(result) for result in results}) == len(results)
    assert all(evidence.strip() for _, _, evidence in results)


@pytest.mark.parametrize(
    "manifest",
    (
        {},
        {"schema_version": "mercury.phase15-certification/v0", "required_gates": list(REQUIRED_PHASE15_GATE_IDS)},
        {"schema_version": "mercury.phase15-certification/v1", "required_gates": list(REQUIRED_PHASE15_GATE_IDS[:-1])},
        {"schema_version": "mercury.phase15-certification/v1", "required_gates": [*REQUIRED_PHASE15_GATE_IDS, "unknown"]},
        {"schema_version": "mercury.phase15-certification/v1", "required_gates": [*REQUIRED_PHASE15_GATE_IDS, REQUIRED_PHASE15_GATE_IDS[0]]},
    ),
)
def test_phase15_certification_fails_closed_for_malformed_missing_duplicate_or_unknown_manifest(tmp_path, manifest):
    path = tmp_path / "phase15.json"
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="invalid phase15 manifest"):
        evaluate(config_path=path)


def test_phase15_certification_fails_closed_for_missing_manifest(tmp_path):
    with pytest.raises(ValueError, match="phase15 manifest unavailable"):
        evaluate(config_path=tmp_path / "missing.json")
