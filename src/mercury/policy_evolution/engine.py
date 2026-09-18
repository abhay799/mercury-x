from mercury.policy_evolution.contracts import PromotionDecision, PromotionState

class PolicyEvolutionEngine:
    def evaluate_for_shadow(self, candidate):
        safe = all((candidate.quality_floor_preserved,candidate.safety_preserved,candidate.fairness_preserved,candidate.authorization_preserved))
        return PromotionDecision(
            decision_id=f"shadow:{candidate.policy_candidate_id}",
            policy_candidate_id=candidate.policy_candidate_id,
            state=PromotionState.SHADOW if safe else PromotionState.REJECTED,
            human_approval_required=True,
            human_approval_id=None,
            reason_codes=("SAFE_FOR_SHADOW",) if safe else ("HARD_INVARIANT_FAILED",),
        )

    def approve_for_production(self, candidate, *, approval_id:str|None):
        if not approval_id or not approval_id.strip():
            raise ValueError("human approval required")
        if not candidate.shadow_evidence_ids or not candidate.canary_evidence_ids:
            raise ValueError("shadow and canary evidence required")
        if not all((candidate.quality_floor_preserved,candidate.safety_preserved,candidate.fairness_preserved,candidate.authorization_preserved)):
            raise ValueError("hard invariant failed")
        return PromotionDecision(
            decision_id=f"approve:{candidate.policy_candidate_id}",
            policy_candidate_id=candidate.policy_candidate_id,
            state=PromotionState.APPROVED,
            human_approval_required=True,
            human_approval_id=approval_id,
            reason_codes=("CONTROLLED_PROMOTION_APPROVED",),
        )
