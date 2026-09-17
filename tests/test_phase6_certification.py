import json
from pathlib import Path
import pytest
from mercury.certification.phase6 import Phase6CertificationConfig, Phase6Gate, REQUIRED_PHASE6_GATE_IDS, evaluate_phase6_certification

def complete(): return Phase6CertificationConfig(gates=tuple(Phase6Gate(gate_id=item,passed=True,evidence="verified") for item in REQUIRED_PHASE6_GATE_IDS))
def test_complete_certification_passes_all_required_gates():
    result=evaluate_phase6_certification(complete())
    assert result.overall_passed and result.passed_gate_count==18 and result.failed_gate_count==0
def test_missing_or_failed_gate_fails_closed():
    assert not evaluate_phase6_certification(Phase6CertificationConfig(gates=complete().gates[:-1])).overall_passed
    assert not evaluate_phase6_certification(complete().model_copy(update={"gates":(Phase6Gate(gate_id=REQUIRED_PHASE6_GATE_IDS[0],passed=False,evidence="failure"),*complete().gates[1:])})).overall_passed
def test_blank_evidence_duplicate_and_unknown_gate_rejected():
    with pytest.raises(Exception): Phase6Gate(gate_id="x",passed=True,evidence="")
    with pytest.raises(Exception): Phase6CertificationConfig(gates=(complete().gates[0],complete().gates[0]))
    with pytest.raises(Exception): Phase6CertificationConfig(gates=(Phase6Gate(gate_id="unknown",passed=True,evidence="x"),))
def test_result_is_immutable_and_deterministic():
    first=evaluate_phase6_certification(complete()); second=evaluate_phase6_certification(complete())
    assert first==second
    with pytest.raises(Exception): first.overall_passed=False
