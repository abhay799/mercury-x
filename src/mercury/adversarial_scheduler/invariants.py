def challenge_passes(result) -> bool:
    return result.invariant_preserved and not result.starvation_detected and not result.quality_degraded and not result.authority_leak_detected
