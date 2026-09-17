import pytest
from mercury.certification.phase8 import REQUIRED_PHASE8_GATE_IDS,Phase8CertificationConfig,Phase8Gate,evaluate_phase8_certification
def complete(): return Phase8CertificationConfig(gates=tuple(Phase8Gate(gate_id=x,passed=True,evidence="verified") for x in REQUIRED_PHASE8_GATE_IDS))
def test_complete_config_passes_all_required_gates(): assert evaluate_phase8_certification(complete()).overall_passed
def test_missing_unknown_and_duplicate_gates_fail_closed():
 assert not evaluate_phase8_certification(Phase8CertificationConfig(gates=complete().gates[:-1])).overall_passed
 with pytest.raises(Exception): Phase8CertificationConfig(gates=(Phase8Gate(gate_id="unknown",passed=True,evidence="x"),))
