from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from typing import Literal

from pydantic import Field, model_validator

from mercury.contracts.base import ContractModel


_SHA256_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
ReadinessStatus = Literal["READY", "PLANNED", "MISSING", "STALE", "UNVERIFIED"]


class ArtifactRecord(ContractModel):
    """Registered metadata for a repository artifact required by the master spec."""

    artifact_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    path: str = Field(min_length=1)
    creator: str = Field(min_length=1)
    consumers: list[str] = Field(min_length=1)
    artifact_schema_version: str = Field(min_length=1)
    artifact_version: str = Field(min_length=1)
    required: bool
    checksum: str = Field(min_length=1)
    readiness: ReadinessStatus

    @model_validator(mode="after")
    def validate_relative_path_and_checksum(self):
        path = PurePosixPath(self.path)
        if (
            "\\" in self.path
            or path.is_absolute()
            or ".." in path.parts
            or (path.parts and ":" in path.parts[0])
        ):
            raise ValueError("artifact path must be a safe relative POSIX path")
        if not _SHA256_PATTERN.fullmatch(self.checksum):
            raise ValueError("artifact checksum must be a sha256:<lowercase-hex> value")
        return self


class ArtifactManifest(ContractModel):
    schema_version: Literal["mercury.artifact.manifest/v1"] = "mercury.artifact.manifest/v1"
    manifest_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    artifacts: list[ArtifactRecord] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unique_artifact_ids(self):
        artifact_ids = [artifact.artifact_id for artifact in self.artifacts]
        if len(artifact_ids) != len(set(artifact_ids)):
            raise ValueError("duplicate artifact_id")
        return self


class ArtifactManifestResult(ContractModel):
    manifest_id: str = Field(min_length=1)
    passed: bool
    artifact_reasons: dict[str, str] = Field(default_factory=dict)
    missing_required_artifacts: list[str] = Field(default_factory=list)


def load_artifact_manifest(path: str | Path) -> ArtifactManifest:
    with Path(path).open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return ArtifactManifest.model_validate(payload)


def evaluate_artifact_manifest(
    manifest: ArtifactManifest, repository_root: str | Path
) -> ArtifactManifestResult:
    root = Path(repository_root).resolve()
    reasons: dict[str, str] = {}
    missing_required: list[str] = []

    for artifact in manifest.artifacts:
        artifact_path = (root / PurePosixPath(artifact.path)).resolve()
        reason = _validate_artifact(artifact, artifact_path, root)
        reasons[artifact.artifact_id] = reason
        if artifact.required and reason != "valid":
            missing_required.append(artifact.artifact_id)

    return ArtifactManifestResult(
        manifest_id=manifest.manifest_id,
        passed=not missing_required,
        artifact_reasons=reasons,
        missing_required_artifacts=missing_required,
    )


def _validate_artifact(
    artifact: ArtifactRecord, artifact_path: Path, repository_root: Path
) -> str:
    try:
        artifact_path.relative_to(repository_root)
    except ValueError:
        return "artifact path resolves outside repository root"

    if artifact.readiness != "READY":
        return f"artifact readiness is {artifact.readiness}, not READY"
    if not artifact_path.is_file():
        return f"artifact path not found: {artifact.path}"
    if _sha256(artifact_path) != artifact.checksum:
        return "checksum mismatch"
    return "valid"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65_536), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"
