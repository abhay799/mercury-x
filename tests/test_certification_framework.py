import hashlib
import json
from pathlib import Path
import pytest
from pydantic import ValidationError

from mercury.certification.config_loader import load_certification_checklist
from mercury.certification.evaluator import evaluate_certification
from mercury.certification.models import CertificationChecklist, CertificationItem, CertificationResult

CONFIG = Path("configs/certification/preflight.json")
MANIFEST_CONFIG = Path("configs/artifacts/manifest.json")
CERTIFICATION_RECORD = Path("configs/certification/preflight-record.json")
MASTER_SPEC_PREFLIGHT_ITEM_IDS = {
    "architecture",
    "scope",
    "schemas",
    "interfaces",
    "policies",
    "registries",
    "artifact_manifest",
    "environment",
    "dependency_lock",
    "repository_structure",
    "cpu_strategy",
    "remote_gpu_strategy",
    "benchmarks",
    "slos",
    "telemetry",
    "failure_model",
    "security",
    "testing",
    "certification",
    "cloud_budget_controls",
    "documentation",
}

def test_preflight_checklist_loads():
    checklist = load_certification_checklist(CONFIG)
    assert checklist.checklist_id == "mercury.preflight/v1"
    assert {item.item_id for item in checklist.items} == MASTER_SPEC_PREFLIGHT_ITEM_IDS

def test_all_required_pass_means_certified():
    checklist = load_certification_checklist(CONFIG)
    statuses = {item.item_id: "PASS" for item in checklist.items}
    result = evaluate_certification(checklist, statuses)
    assert result.passed is True
    assert result.missing_required_items == []

def test_missing_required_item_fails_closed():
    checklist = load_certification_checklist(CONFIG)
    statuses = {item.item_id: "PASS" for item in checklist.items if item.item_id != "security"}
    result = evaluate_certification(checklist, statuses)
    assert result.passed is False
    assert "security" in result.missing_required_items
    assert result.statuses["security"] == "NOT_RUN"

def test_explicit_failure_is_reported():
    checklist = load_certification_checklist(CONFIG)
    statuses = {item.item_id: "PASS" for item in checklist.items}
    statuses["benchmarks"] = "FAIL"
    result = evaluate_certification(checklist, statuses)
    assert result.passed is False
    assert result.missing_required_items == ["benchmarks"]

def test_duplicate_checklist_items_are_rejected():
    item = CertificationItem(item_id="x", description="x")
    with pytest.raises(ValueError):
        CertificationChecklist(checklist_id="test", items=[item, item])


def test_certification_rejects_unknown_statuses_and_passing_record_requires_evidence():
    from mercury.certification.models import CertificationRecord

    checklist = load_certification_checklist(CONFIG)
    statuses = {item.item_id: "PASS" for item in checklist.items}

    with pytest.raises(ValueError, match="unknown certification status"):
        evaluate_certification(checklist, {**statuses, "unknown": "PASS"})

    with pytest.raises(ValueError, match="nonblank evidence"):
        CertificationRecord(
            record_id="invalid-empty-evidence",
            checklist_id=checklist.checklist_id,
            statuses={"unbound": "PASS"},
            evidence={"unbound": [" "]},
        )

    result = evaluate_certification(checklist, statuses)
    evidence = {item.item_id: [f"evidence for {item.item_id}"] for item in checklist.items}
    record = CertificationRecord.from_result(
        record_id="mercury.preflight.record/v1",
        checklist=checklist,
        result=result,
        evidence=evidence,
    )

    assert record.passed is True
    assert record.statuses == statuses

    failed_result = evaluate_certification(
        checklist,
        {**statuses, "security": "FAIL"},
    )
    with pytest.raises(ValueError, match="passing certification record"):
        CertificationRecord.from_result(
            record_id="mercury.preflight.record/v1",
            checklist=checklist,
            result=failed_result,
            evidence=evidence,
        )

    with pytest.raises(ValueError, match="unknown certification status"):
        CertificationRecord.from_result(
            record_id="invalid-unknown-status",
            checklist=checklist,
            result=CertificationResult(
                checklist_id=checklist.checklist_id,
                statuses={"unknown": "PASS"},
                passed=True,
            ),
            evidence={"unknown": ["invalid"]},
        )


def test_certification_record_loader_requires_complete_checklist_coverage(tmp_path):
    from mercury.certification.config_loader import load_certification_record

    checklist = load_certification_checklist(CONFIG)
    record_path = tmp_path / "incomplete-preflight-record.json"
    record_path.write_text(
        json.dumps(
            {
                "record_id": "incomplete",
                "checklist_id": checklist.checklist_id,
                "statuses": {"architecture": "PASS"},
                "passed": True,
                "evidence": {"architecture": ["evidence"]},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="complete certification status coverage"):
        load_certification_record(record_path, checklist)

    record_path.write_text(
        json.dumps(
            {
                "record_id": "unknown",
                "checklist_id": checklist.checklist_id,
                "statuses": {
                    **{item.item_id: "PASS" for item in checklist.items},
                    "unknown": "PASS",
                },
                "passed": True,
                "evidence": {
                    **{item.item_id: ["evidence"] for item in checklist.items},
                    "unknown": ["evidence"],
                },
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unknown certification status"):
        load_certification_record(record_path, checklist)


def test_artifact_manifest_loads_and_validates_required_artifacts():
    from mercury.certification.artifact_manifest import (
        evaluate_artifact_manifest,
        load_artifact_manifest,
    )

    manifest = load_artifact_manifest(MANIFEST_CONFIG)
    result = evaluate_artifact_manifest(manifest, Path("."))

    assert manifest.schema_version == "mercury.artifact.manifest/v1"
    assert result.passed is True
    assert result.missing_required_artifacts == []


def test_artifact_manifest_rejects_unsafe_paths_and_duplicate_ids(tmp_path):
    from mercury.certification.artifact_manifest import ArtifactManifest, ArtifactRecord

    checksum = f"sha256:{hashlib.sha256(b'canonical artifact').hexdigest()}"
    record = ArtifactRecord(
        artifact_id="artifact-1",
        name="Canonical artifact",
        path="docs/canonical.md",
        creator="test",
        consumers=["test"],
        artifact_schema_version="document/v1",
        artifact_version="1",
        required=True,
        checksum=checksum,
        readiness="READY",
    )

    with pytest.raises(ValidationError):
        ArtifactRecord(
            artifact_id="unsafe",
            name="Unsafe artifact",
            path="../outside.md",
            creator="test",
            consumers=["test"],
            artifact_schema_version="document/v1",
            artifact_version="1",
            required=True,
            checksum=checksum,
            readiness="READY",
        )

    with pytest.raises(ValueError):
        ArtifactManifest(
            manifest_id="duplicate-artifacts",
            version="1",
            artifacts=[record, record],
        )


def test_artifact_manifest_fails_closed_for_required_integrity_errors(tmp_path):
    from mercury.certification.artifact_manifest import (
        ArtifactManifest,
        ArtifactRecord,
        evaluate_artifact_manifest,
    )

    artifact_path = tmp_path / "docs" / "canonical.md"
    artifact_path.parent.mkdir()
    artifact_path.write_text("canonical artifact", encoding="utf-8")
    matching_checksum = f"sha256:{hashlib.sha256(b'canonical artifact').hexdigest()}"

    manifest = ArtifactManifest(
        manifest_id="test-manifest",
        version="1",
        artifacts=[
            ArtifactRecord(
                artifact_id="matching",
                name="Matching artifact",
                path="docs/canonical.md",
                creator="test",
                consumers=["test"],
                artifact_schema_version="document/v1",
                artifact_version="1",
                required=True,
                checksum=matching_checksum,
                readiness="READY",
            ),
            ArtifactRecord(
                artifact_id="wrong-checksum",
                name="Wrong checksum artifact",
                path="docs/canonical.md",
                creator="test",
                consumers=["test"],
                artifact_schema_version="document/v1",
                artifact_version="1",
                required=True,
                checksum=f"sha256:{'0' * 64}",
                readiness="READY",
            ),
            ArtifactRecord(
                artifact_id="required-missing",
                name="Required missing artifact",
                path="docs/required-missing.md",
                creator="test",
                consumers=["test"],
                artifact_schema_version="document/v1",
                artifact_version="1",
                required=True,
                checksum=matching_checksum,
                readiness="READY",
            ),
            ArtifactRecord(
                artifact_id="optional-missing",
                name="Optional missing artifact",
                path="docs/missing.md",
                creator="test",
                consumers=["test"],
                artifact_schema_version="document/v1",
                artifact_version="1",
                required=False,
                checksum=matching_checksum,
                readiness="PLANNED",
            ),
        ],
    )

    result = evaluate_artifact_manifest(manifest, tmp_path)

    assert result.passed is False
    assert result.missing_required_artifacts == ["wrong-checksum", "required-missing"]
    assert "checksum mismatch" in result.artifact_reasons["wrong-checksum"]
    assert "artifact path not found" in result.artifact_reasons["required-missing"]
    assert "optional-missing" not in result.missing_required_artifacts


def test_passing_preflight_record_matches_the_complete_checklist():
    from mercury.certification.config_loader import load_certification_record

    checklist = load_certification_checklist(CONFIG)
    record = load_certification_record(CERTIFICATION_RECORD, checklist)
    result = evaluate_certification(checklist, record.statuses)

    assert record.passed is True
    assert result.passed is True
    assert set(record.evidence) == {item.item_id for item in checklist.items}


def test_loaded_certification_record_is_immutable_after_validation():
    from mercury.certification.config_loader import load_certification_record

    checklist = load_certification_checklist(CONFIG)
    record = load_certification_record(CERTIFICATION_RECORD, checklist)

    with pytest.raises(TypeError):
        record.statuses.pop("security")
    with pytest.raises(AttributeError):
        record.evidence["security"].append("mutated after validation")
