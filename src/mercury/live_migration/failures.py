
def classify_failure(*, checkpoint_corrupt=False, destination_unavailable=False, transfer_incomplete=False, verification_failed=False, stale=False) -> str:
    if stale:
        return "STALE"
    if checkpoint_corrupt:
        return "CHECKPOINT_CORRUPT"
    if destination_unavailable:
        return "DESTINATION_UNAVAILABLE"
    if transfer_incomplete:
        return "TRANSFER_INCOMPLETE"
    if verification_failed:
        return "VERIFICATION_FAILED"
    return "UNKNOWN_FAILURE"
