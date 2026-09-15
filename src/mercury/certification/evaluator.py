from mercury.certification.models import (
    CertificationChecklist,
    CertificationRecord,
    CertificationResult,
    CertificationStatus,
)

def evaluate_certification(
    checklist: CertificationChecklist,
    statuses: dict[str, CertificationStatus],
) -> CertificationResult:
    known_item_ids = {item.item_id for item in checklist.items}
    unknown_item_ids = set(statuses) - known_item_ids
    if unknown_item_ids:
        unknown_ids = ", ".join(sorted(unknown_item_ids))
        raise ValueError(f"unknown certification status item_id: {unknown_ids}")

    missing_required = []
    for item in checklist.items:
        status = statuses.get(item.item_id, "NOT_RUN")
        if item.required and status != "PASS":
            missing_required.append(item.item_id)

    normalized = {
        item.item_id: statuses.get(item.item_id, "NOT_RUN")
        for item in checklist.items
    }

    return CertificationResult(
        checklist_id=checklist.checklist_id,
        statuses=normalized,
        passed=not missing_required,
        missing_required_items=missing_required,
    )


def validate_certification_record(
    checklist: CertificationChecklist,
    record: CertificationRecord,
) -> CertificationResult:
    """Bind a passing record to the complete, named checklist before trusting it."""

    if record.checklist_id != checklist.checklist_id:
        raise ValueError("certification record checklist_id does not match the supplied checklist")

    expected_item_ids = {item.item_id for item in checklist.items}
    unknown_item_ids = set(record.statuses) - expected_item_ids
    if unknown_item_ids:
        unknown_ids = ", ".join(sorted(unknown_item_ids))
        raise ValueError(f"unknown certification status item_id: {unknown_ids}")

    missing_item_ids = expected_item_ids - set(record.statuses)
    if missing_item_ids:
        missing_ids = ", ".join(sorted(missing_item_ids))
        raise ValueError(
            "passing certification record requires complete certification status coverage; "
            f"missing item_id: {missing_ids}"
        )

    result = evaluate_certification(checklist, record.statuses)
    if not result.passed:
        raise ValueError("passing certification record cannot contain a failed or unrun required status")

    if set(record.evidence) != expected_item_ids:
        raise ValueError("passing certification record requires complete certification evidence coverage")

    return result
