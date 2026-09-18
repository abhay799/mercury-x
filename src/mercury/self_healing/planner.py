from mercury.self_healing.contracts import HealingCandidate

def choose_healing_candidate(candidates: tuple[HealingCandidate, ...]) -> HealingCandidate:
    safe = [c for c in candidates if c.preserves_quality and c.preserves_safety and c.preserves_authorization and c.preserves_privacy]
    if not safe:
        raise ValueError("no safe healing candidate")
    safe.sort(key=lambda c: (not c.reversible, c.estimated_recovery_generations, c.required_resources, c.candidate_id))
    return safe[0]
