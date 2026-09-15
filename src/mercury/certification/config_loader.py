import json
from pathlib import Path
from mercury.certification.models import CertificationChecklist, CertificationRecord
from mercury.certification.evaluator import validate_certification_record

def load_certification_checklist(path: str | Path) -> CertificationChecklist:
    with Path(path).open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return CertificationChecklist.model_validate(payload)


def load_certification_record(
    path: str | Path,
    checklist: CertificationChecklist,
) -> CertificationRecord:
    with Path(path).open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    record = CertificationRecord.model_validate(payload)
    validate_certification_record(checklist, record)
    return record
