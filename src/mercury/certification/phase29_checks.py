from mercury.control_intelligence.contracts import ControlObjective, ControlSignal
from mercury.control_intelligence.engine import ControlIntelligenceEngine


def human_control_gate():
    objective = ControlObjective(
        objective_id="obj-1",
        name="safety-first",
        hard_constraints=("privacy", "safety", "authorization"),
        evidence_quality=0.2,
        provenance_ids=("e1",),
    )
    signal = ControlSignal(
        signal_id="sig-1",
        name="resource_pressure",
        value=0.8,
        provenance_ids=("e1",),
    )
    decision = ControlIntelligenceEngine().resolve(objective, (signal,), allow_autonomous=False)
    return decision.human_escalation_required and decision.action == "DEFER", "control intelligence defers and escalates under uncertain evidence"


CHECKS = {"human_control_gate": human_control_gate}
