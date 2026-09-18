
def validate_security_state(
    *, source_authorization_context_id: str, destination_authorization_context_id: str,
    source_authorization_generation: int, destination_authorization_generation: int,
    destination_expands_authority: bool,
) -> tuple[bool, str]:
    if destination_expands_authority:
        return False, "AUTHORITY_EXPANSION_FORBIDDEN"
    if source_authorization_context_id != destination_authorization_context_id:
        return False, "AUTHORIZATION_CONTEXT_MISMATCH"
    if source_authorization_generation != destination_authorization_generation:
        return False, "AUTHORIZATION_GENERATION_MISMATCH"
    return True, "AUTHORIZATION_PRESERVED"
