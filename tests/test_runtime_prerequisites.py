from __future__ import annotations

import pytest
from pydantic import ValidationError

from mercury.runtime.prerequisites import (
    PrerequisiteCheck,
    PrerequisiteKind,
    PrerequisiteStatus,
    PrerequisiteValidationResult,
    RequiredArtifact,
)


CHECKSUM = "sha256:" + "b" * 64


def artifact(**overrides: object) -> RequiredArtifact:
    values: dict[str, object] = {
        "artifact_id": "model-1",
        "kind": PrerequisiteKind.MODEL_ARTIFACT,
        "required": True,
        "integrity_evidence_required": True,
    }
    values.update(overrides)
    return RequiredArtifact(**values)


def check(**overrides: object) -> PrerequisiteCheck:
    values: dict[str, object] = {
        "artifact_id": "model-1",
        "status": PrerequisiteStatus.READY,
        "checksum": CHECKSUM,
    }
    values.update(overrides)
    return PrerequisiteCheck(**values)


def result(**overrides: object) -> PrerequisiteValidationResult:
    values: dict[str, object] = {
        "workload_id": "workload-1",
        "execution_id": "execution-1",
        "required_artifacts": (artifact(),),
        "checks": (check(),),
    }
    values.update(overrides)
    return PrerequisiteValidationResult(**values)


def test_valid_required_artifacts_pass():
    assert result().passed is True


def test_missing_required_artifact_fails():
    assert result(checks=()).passed is False


def test_required_artifact_not_ready_fails():
    failed_check = check(status=PrerequisiteStatus.MISSING, reason="artifact is unavailable")
    assert result(checks=(failed_check,)).passed is False


@pytest.mark.parametrize("checksum", [None, "sha256:" + "B" * 64])
def test_invalid_or_missing_checksum_fails_when_integrity_evidence_is_required(checksum: str | None):
    assert result(checks=(check(checksum=checksum),)).passed is False


def test_optional_missing_artifact_does_not_fail_validation():
    optional = artifact(required=False)
    missing = check(status=PrerequisiteStatus.MISSING, reason="optional artifact unavailable")
    assert result(required_artifacts=(optional,), checks=(missing,)).passed is True


def test_duplicate_artifact_ids_are_rejected():
    item = artifact()
    with pytest.raises(ValidationError):
        result(required_artifacts=(item, item))


def test_blank_artifact_ids_are_rejected():
    with pytest.raises(ValidationError):
        artifact(artifact_id=" ")


def test_every_failed_check_has_an_explicit_reason():
    with pytest.raises(ValidationError):
        check(status=PrerequisiteStatus.MISSING)


def test_result_and_check_collections_are_immutable():
    validation = result()
    assert isinstance(validation.checks, tuple)
    with pytest.raises((AttributeError, TypeError, ValidationError)):
        validation.checks += (check(),)


def test_validation_result_preserves_workload_execution_identity_and_evidence():
    validation = result()
    assert validation.workload_id == "workload-1"
    assert validation.execution_id == "execution-1"
    assert validation.checks[0].checksum == CHECKSUM
