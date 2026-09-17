from mercury.compute_negotiator.contracts import NegotiationLifecycle
_ALLOWED={
NegotiationLifecycle.REQUESTED:{NegotiationLifecycle.EVALUATING,NegotiationLifecycle.REJECTED},
NegotiationLifecycle.EVALUATING:{NegotiationLifecycle.OFFERED,NegotiationLifecycle.COUNTEROFFERED,NegotiationLifecycle.REJECTED,NegotiationLifecycle.UNKNOWN},
NegotiationLifecycle.OFFERED:{NegotiationLifecycle.ACCEPTED,NegotiationLifecycle.REJECTED,NegotiationLifecycle.EXPIRED,NegotiationLifecycle.REVOKED},
NegotiationLifecycle.COUNTEROFFERED:{NegotiationLifecycle.ACCEPTED,NegotiationLifecycle.REJECTED,NegotiationLifecycle.EXPIRED,NegotiationLifecycle.REVOKED},
NegotiationLifecycle.ACCEPTED:{NegotiationLifecycle.REVOKED},
}
def transition_lifecycle(current,target):
    if target not in _ALLOWED.get(current,set()): raise ValueError("illegal negotiation transition")
    return target
