def should_revoke(*,resource_envelope_available,authorization_valid,hard_constraints_still_hold):
    if not resource_envelope_available:return True,"RESOURCE_ENVELOPE_LOST"
    if not authorization_valid:return True,"AUTHORIZATION_REVOKED"
    if not hard_constraints_still_hold:return True,"HARD_CONSTRAINT_DRIFT"
    return False,"AGREEMENT_STILL_VALID"
