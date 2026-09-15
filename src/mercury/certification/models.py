from typing import Any, Literal
from pydantic import Field, model_validator
from mercury.contracts.base import ContractModel

CertificationStatus = Literal["PASS", "FAIL", "NOT_RUN"]


class _FrozenDict(dict[str, Any]):
    """JSON-serializable mapping that rejects post-validation mutation."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        dict.__init__(self, *args, **kwargs)

    def _immutable(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError("certification record is immutable after validation")

    __setitem__ = _immutable
    __delitem__ = _immutable
    clear = _immutable
    pop = _immutable
    popitem = _immutable
    setdefault = _immutable
    update = _immutable
    __ior__ = _immutable


class CertificationItem(ContractModel):
    item_id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    required: bool = True

class CertificationChecklist(ContractModel):
    checklist_id: str = Field(min_length=1)
    items: list[CertificationItem] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unique_ids(self):
        ids = [item.item_id for item in self.items]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate certification item_id")
        return self

class CertificationResult(ContractModel):
    checklist_id: str
    statuses: dict[str, CertificationStatus]
    passed: bool
    missing_required_items: list[str] = Field(default_factory=list)


class CertificationRecord(ContractModel):
    """Evidence-backed record that may exist only for a fully passing gate."""

    record_id: str = Field(min_length=1)
    checklist_id: str = Field(min_length=1)
    statuses: dict[str, CertificationStatus] = Field(min_length=1)
    passed: Literal[True] = True
    evidence: dict[str, list[str]] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_passing_evidence(self):
        if any(status != "PASS" for status in self.statuses.values()):
            raise ValueError("passing certification record requires every status to be PASS")
        if set(self.evidence) != set(self.statuses):
            raise ValueError("certification evidence keys must match certification statuses")
        if any(not entries for entries in self.evidence.values()):
            raise ValueError("passing certification record requires evidence for every status")
        if any(not entry.strip() for entries in self.evidence.values() for entry in entries):
            raise ValueError("passing certification record requires nonblank evidence for every status")
        object.__setattr__(self, "statuses", _FrozenDict(self.statuses))
        object.__setattr__(
            self,
            "evidence",
            _FrozenDict({item_id: tuple(entries) for item_id, entries in self.evidence.items()}),
        )
        return self

    @classmethod
    def from_result(
        cls,
        *,
        record_id: str,
        checklist: CertificationChecklist,
        result: CertificationResult,
        evidence: dict[str, list[str]],
    ) -> "CertificationRecord":
        if not result.passed:
            raise ValueError("passing certification record cannot be created from a failed result")
        record = cls(
            record_id=record_id,
            checklist_id=result.checklist_id,
            statuses=result.statuses,
            evidence=evidence,
        )
        from mercury.certification.evaluator import validate_certification_record

        validate_certification_record(checklist, record)
        return record
