from __future__ import annotations

import re
from enum import Enum

from pydantic import field_validator, model_validator

from mercury.contracts.base import ContractModel


_SHA256_EVIDENCE = re.compile(r"sha256:[0-9a-f]{64}")


class PrerequisiteKind(str, Enum):
    MODEL_ARTIFACT = "model_artifact"
    CONTEXT_ARTIFACT = "context_artifact"
    CHECKPOINT = "checkpoint"
    MODEL_CONFIGURATION = "model_configuration"
    HARDWARE_PLACEMENT = "hardware_placement"


class PrerequisiteStatus(str, Enum):
    READY = "ready"
    MISSING = "missing"
    INVALID = "invalid"
    UNAVAILABLE = "unavailable"


class RequiredArtifact(ContractModel):
    artifact_id: str
    kind: PrerequisiteKind
    required: bool = True
    integrity_evidence_required: bool = False

    @field_validator("artifact_id")
    @classmethod
    def artifact_id_is_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("artifact id must be non-empty")
        return value


class PrerequisiteCheck(ContractModel):
    artifact_id: str
    status: PrerequisiteStatus
    checksum: str | None = None
    reason: str | None = None

    @field_validator("artifact_id", "reason")
    @classmethod
    def text_is_non_empty_when_present(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("text must be non-empty")
        return value

    @model_validator(mode="after")
    def failed_checks_have_evidence(self) -> PrerequisiteCheck:
        if self.status is not PrerequisiteStatus.READY and not self.reason:
            raise ValueError("failed check requires an explicit reason")
        return self


class PrerequisiteValidationResult(ContractModel):
    workload_id: str
    execution_id: str
    required_artifacts: tuple[RequiredArtifact, ...]
    checks: tuple[PrerequisiteCheck, ...]

    @field_validator("workload_id", "execution_id")
    @classmethod
    def identities_are_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("identity must be non-empty")
        return value

    @model_validator(mode="after")
    def required_artifact_ids_are_unique(self) -> PrerequisiteValidationResult:
        artifact_ids = tuple(item.artifact_id for item in self.required_artifacts)
        if len(artifact_ids) != len(set(artifact_ids)):
            raise ValueError("artifact ids must be unique")
        return self

    @property
    def passed(self) -> bool:
        checks_by_id = {check.artifact_id: check for check in self.checks}
        for artifact in self.required_artifacts:
            check = checks_by_id.get(artifact.artifact_id)
            if not artifact.required:
                continue
            if check is None or check.status is not PrerequisiteStatus.READY:
                return False
            if artifact.integrity_evidence_required and not _SHA256_EVIDENCE.fullmatch(check.checksum or ""):
                return False
        return True
