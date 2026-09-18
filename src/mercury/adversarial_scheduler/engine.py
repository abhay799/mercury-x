from mercury.adversarial_scheduler.contracts import SchedulerChallengeResult

class AdversarialScheduler:
    def evaluate(self, scenario, *, invariant_preserved:bool, starvation_detected:bool,
                 quality_degraded:bool, authority_leak_detected:bool):
        reasons=[]
        if starvation_detected: reasons.append("STARVATION")
        if quality_degraded: reasons.append("QUALITY_DEGRADATION")
        if authority_leak_detected: reasons.append("AUTHORITY_LEAK")
        if not invariant_preserved: reasons.append("SCHEDULER_INVARIANT_BROKEN")
        if not reasons: reasons.append("ROBUST")
        return SchedulerChallengeResult(
            result_id=f"adv:{scenario.scenario_id}",
            scenario_id=scenario.scenario_id,
            invariant_preserved=invariant_preserved,
            starvation_detected=starvation_detected,
            quality_degraded=quality_degraded,
            authority_leak_detected=authority_leak_detected,
            reason_codes=tuple(reasons),
        )
