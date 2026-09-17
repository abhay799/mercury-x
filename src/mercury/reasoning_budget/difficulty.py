from mercury.contracts.base import ContractModel
from mercury.reasoning_budget.contracts import WorkloadDifficulty, canonical_hash

class DifficultyEvidence(ContractModel):
    evidence_id: str
    feature_name: str
    normalized_value: float
    verified: bool = True

class DifficultyAssessment(ContractModel):
    assessment_id: str
    difficulty: WorkloadDifficulty
    evidence_ids: tuple[str, ...]
    reason_codes: tuple[str, ...]

def estimate_difficulty(evidence):
    verified = tuple(sorted((e for e in evidence if e.verified), key=lambda e:e.evidence_id))
    if not verified:
        diff=WorkloadDifficulty.UNKNOWN; reasons=("INSUFFICIENT_EVIDENCE",)
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
    return DifficultyAssessment(
        assessment_id=canonical_hash({"difficulty":diff.value,"evidence_ids":ids}),
        difficulty=diff,evidence_ids=ids,reason_codes=reasons)
