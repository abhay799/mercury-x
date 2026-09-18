from mercury.self_healing.contracts import HealingLifecycle
_ALLOWED = {
    HealingLifecycle.DETECTED:{HealingLifecycle.DIAGNOSING,HealingLifecycle.UNKNOWN,HealingLifecycle.FAILED},
    HealingLifecycle.DIAGNOSING:{HealingLifecycle.PLANNED,HealingLifecycle.UNKNOWN,HealingLifecycle.FAILED},
    HealingLifecycle.PLANNED:{HealingLifecycle.AUTHORIZED,HealingLifecycle.FAILED},
    HealingLifecycle.AUTHORIZED:{HealingLifecycle.EXECUTING,HealingLifecycle.FAILED},
    HealingLifecycle.EXECUTING:{HealingLifecycle.VERIFYING,HealingLifecycle.ROLLED_BACK,HealingLifecycle.FAILED},
    HealingLifecycle.VERIFYING:{HealingLifecycle.RECOVERED,HealingLifecycle.ROLLED_BACK,HealingLifecycle.FAILED},
}
def transition(current, target):
    if target not in _ALLOWED.get(current,set()):
        raise ValueError(f"illegal healing transition {current}->{target}")
    return target
