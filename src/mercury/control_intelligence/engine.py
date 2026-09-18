from mercury.control_intelligence.contracts import ControlDecision, ControlObjective, ControlSignal


class ControlIntelligenceEngine:
    def resolve(
        self,
        objective: ControlObjective | str | None = None,
        signals: tuple[ControlSignal, ...] | tuple[tuple[str, float], ...] = (),
        *,
        objective_id: str | None = None,
        objective_name: str | None = None,
        hard_constraints: tuple[str, ...] = (),
        evidence_quality: float = 0.0,
        provenance_ids: tuple[str, ...] = (),
        allow_autonomous: bool = False,
    ) -> ControlDecision:
        if isinstance(objective, str):
            objective = ControlObjective(
                objective_id=objective,
                name=objective_name or "default-objective",
                hard_constraints=hard_constraints,
                evidence_quality=evidence_quality,
                provenance_ids=provenance_ids,
            )
        if objective is None:
            objective = ControlObjective(
                objective_id=objective_id or "default-objective",
                name=objective_name or "default-objective",
                hard_constraints=hard_constraints,
                evidence_quality=evidence_quality,
                provenance_ids=provenance_ids,
            )
        signal_values = tuple(float(value) for _, value in signals) if signals and isinstance(signals[0], tuple) else ()
        quality = objective.evidence_quality
        if not allow_autonomous and (quality < 0.5 or not objective.hard_constraints):
            return ControlDecision(
                decision_id=f"control:{objective.objective_id}",
                objective_id=objective.objective_id,
                action="DEFER",
                human_escalation_required=True,
                reason_codes=("LOW_EVIDENCE_QUALITY", "HUMAN_ESCALATION_REQUIRED"),
                evidence_quality=quality,
                allowed_autonomous=False,
            )
        return ControlDecision(
            decision_id=f"control:{objective.objective_id}",
            objective_id=objective.objective_id,
            action="APPLY_SAFE_RECOMMENDATION",
            human_escalation_required=not allow_autonomous,
            reason_codes=("EVIDENCE_ACCEPTED",),
            evidence_quality=quality,
            allowed_autonomous=allow_autonomous,
        )
