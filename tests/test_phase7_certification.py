import pytest
from mercury.certification.phase7 import REQUIRED_PHASE7_GATE_IDS,Phase7CertificationConfig,Phase7Gate,evaluate_phase7_certification
def complete(): return Phase7CertificationConfig(gates=tuple(Phase7Gate(gate_id=x,passed=True,evidence="verified") for x in REQUIRED_PHASE7_GATE_IDS))
def test_complete_config_passes_all_gates():
 result=evaluate_phase7_certification(complete()); assert result.overall_passed and result.passed_gate_count==19 and result.failed_gate_count==0
def test_missing_failed_duplicate_and_unknown_gates_fail_closed():
 assert not evaluate_phase7_certification(Phase7CertificationConfig(gates=complete().gates[:-1])).overall_passed
 with pytest.raises(Exception): Phase7CertificationConfig(gates=(Phase7Gate(gate_id="unknown",passed=True,evidence="x"),))
 with pytest.raises(Exception): Phase7CertificationConfig(gates=(complete().gates[0],complete().gates[0]))
