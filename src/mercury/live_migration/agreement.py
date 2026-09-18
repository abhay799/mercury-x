
from mercury.live_migration.contracts import MigrationAgreementView, MigrationRequest

def validate_agreement(request: MigrationRequest, agreement: MigrationAgreementView) -> tuple[bool, str]:
    if agreement.agreement_id != request.compute_agreement_id:
        return False, "AGREEMENT_ID_MISMATCH"
    if agreement.agreement_generation != request.compute_agreement_generation:
        return False, "AGREEMENT_GENERATION_MISMATCH"
    if agreement.authorization_context_id != request.authorization_context_id:
        return False, "AGREEMENT_AUTHORIZATION_MISMATCH"
    if agreement.authorization_generation != request.authorization_generation:
        return False, "AGREEMENT_AUTHORIZATION_GENERATION_MISMATCH"
    return True, "AGREEMENT_PRESERVED"
