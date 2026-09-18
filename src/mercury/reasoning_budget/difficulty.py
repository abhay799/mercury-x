from mercury.contracts.base import ContractModel
from mercury.reasoning_budget.contracts import WorkloadDifficulty, canonical_hash

class DifficultyEvidence(ContractModel):
    evidence_id: str
    feature_name: str
    normalized_value: float
    verified: bool = True
    operating_domain: str
    provenance_ids: tuple[str, ...]

class DifficultyAssessment(ContractModel):
    assessment_id: str
    difficulty: WorkloadDifficulty
    evidence_ids: tuple[str, ...]
    reason_codes: tuple[str, ...]
    operating_domain: str
    provenance_ids: tuple[str, ...]

def estimate_difficulty(evidence):
    verified = tuple(sorted((e for e in evidence if e.verified), key=lambda e:e.evidence_id))
    domains={e.operating_domain for e in verified}
    if not verified:
        diff=WorkloadDifficulty.UNKNOWN; reasons=("INSUFFICIENT_EVIDENCE",)
    elif len(domains) != 1:
        diff=WorkloadDifficulty.UNKNOWN; reasons=("CONFLICTING_OPERATING_DOMAIN",)
    else:
        vals=[e.normalized_value for e in verified]
        spread=max(vals)-min(vals)
        if spread > 0.65:
            diff=WorkloadDifficulty.UNKNOWN; reasons=("CONFLICTING_DIFFICULTY_EVIDENCE",)
        else:
            avg=sum(vals)/len(vals)
            diff=(WorkloadDifficulty.LOW if avg<.25 else
                  WorkloadDifficulty.MEDIUM if avg<.5 else
                  WorkloadDifficulty.HIGH if avg<.8 else WorkloadDifficulty.EXTREME)
            reasons=("EVIDENCE_BACKED_DIFFICULTY",)
    ids=tuple(e.evidence_id for e in verified)
    provenance=tuple(sorted({p for e in verified for p in e.provenance_ids}))
    return DifficultyAssessment(
        assessment_id=canonical_hash({"difficulty":diff.value,"evidence_ids":ids}),
        difficulty=diff,evidence_ids=ids,reason_codes=reasons,
        operating_domain=next(iter(domains)) if len(domains)==1 else "UNKNOWN",
        provenance_ids=provenance)
