from mercury.control_intelligence.contracts import ControlSignal, ControlObjective, ControlDecision
from mercury.control_intelligence.engine import ControlIntelligenceEngine


def test_control_intelligence_defers_on_unknown_evidence_and_human_escalates():
    objective = ControlObjective(
        objective_id="obj-1",
        name="safety-first",
        hard_constraints=("privacy", "safety", "authorization"),
        evidence_quality=0.2,
        provenance_ids=("e1",),
    )
    sg = ControlSignal(
        signal_id="sig-1",
        name="resource_pressure",
        value=0.8,
        provenance_ids=("e1",),
    )
    decision = ControlIntelligenceEngine().resolve(objective, (sg,), allow_autonomous=False)
    assert decision.decision_id.startswith("control:")
    assert decision.human_escalation_required is True
