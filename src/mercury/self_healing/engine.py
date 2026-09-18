from mercury.self_healing.contracts import HealingDecision
from mercury.self_healing.planner import choose_healing_candidate

class SelfHealingEngine:
    def plan(self, request, candidates, *, decision_generation:int):
        selected = choose_healing_candidate(tuple(candidates))
        return HealingDecision(
            decision_id=f"heal:{request.healing_request_id}:{decision_generation}",
            healing_request_id=request.healing_request_id,
            selected_candidate_id=selected.candidate_id,
            action=selected.action,
            authorized=False,
            reason_codes=("SAFE_CANDIDATE_SELECTED",),
            decision_generation=decision_generation,
        )
