"""Validate the maintained MERCURY X evidence surface."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs" / "evidence" / "EVIDENCE_MANIFEST.json"
REPORT = ROOT / "docs" / "evidence" / "BENCHMARKS_AND_EVIDENCE.md"
RUNNER = ROOT / "scripts" / "evidence" / "run_evidence.py"

EXPECTED_TAXONOMY = {
    "MEASURED",
    "SYNTHETIC",
    "SIMULATED",
    "STATIC_DEMO",
    "UNCALIBRATED",
    "NOT_MEASURED",
}

REQUIRED_REPORT_SECTIONS = (
    "## Purpose",
    "## Evidence taxonomy",
    "## Current evidence summary",
    "## Functional correctness evidence",
    "## Certification evidence",
    "## Safety invariant evidence",
    "## Scenario and demonstration evidence",
    "## Performance evidence",
    "## Simulated evidence",
    "## Uncalibrated components",
    "## Not-measured capabilities",
    "## Reproduction instructions",
    "## Interpretation guidance",
    "## Limitations",
)

REQUIRED_NOT_MEASURED = {
    "gpu_inference_throughput",
    "multi_gpu_scaling",
    "cloud_distributed_throughput",
    "network_transfer_performance",
    "physical_live_migration_downtime",
    "physical_gpu_memory_migration",
    "datacenter_power_savings",
    "production_scheduler_improvement",
    "model_quality_improvement",
    "digital_twin_prediction_accuracy",
    "production_federation_latency",
    "real_world_cost_savings",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> int:
    require(MANIFEST.is_file(), f"missing evidence manifest: {MANIFEST}")
    require(REPORT.is_file(), f"missing evidence report: {REPORT}")
    require(RUNNER.is_file(), f"missing evidence runner: {RUNNER}")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    require(
        manifest.get("schema_version") == "mercury.evidence-manifest/v1",
        "unsupported evidence manifest schema",
    )
    require(set(manifest.get("taxonomy", {})) == EXPECTED_TAXONOMY, "evidence taxonomy mismatch")

    entries = manifest.get("evidence", [])
    require(isinstance(entries, list) and entries, "evidence inventory must be non-empty")
    identifiers = [entry.get("id") for entry in entries]
    require(all(isinstance(item, str) and item.strip() for item in identifiers), "blank evidence id")
    require(len(identifiers) == len(set(identifiers)), "duplicate evidence id")
    for entry in entries:
        classes = entry.get("classifications")
        require(isinstance(classes, list) and classes, f"missing classifications: {entry['id']}")
        require(set(classes) <= EXPECTED_TAXONOMY, f"unknown classification: {entry['id']}")
        require(entry.get("claim_boundary", "").strip(), f"blank claim boundary: {entry['id']}")

    unsupported = manifest.get("unsupported_measurements", [])
    unsupported_ids = {item.get("id") for item in unsupported}
    require(unsupported_ids == REQUIRED_NOT_MEASURED, "NOT_MEASURED inventory mismatch")
    require(
        all(item.get("classification") == "NOT_MEASURED" for item in unsupported),
        "unsupported capability must be NOT_MEASURED",
    )

    report = REPORT.read_text(encoding="utf-8")
    for section in REQUIRED_REPORT_SECTIONS:
        require(section in report, f"missing report section: {section}")
    require("1506" not in report or "HISTORICAL" in report, "historical result is not labeled")
    require("artifacts/evidence/mercury_evidence.json" in report, "snapshot path is undocumented")

    runner_text = RUNNER.read_text(encoding="utf-8")
    require("mercury.evidence-snapshot/v1" in runner_text, "runner snapshot schema missing")
    require("random" not in runner_text.lower(), "runner must not use random data")
    require(
        "safe.directory=C:/Users/DELL/Downloads/Mercury-x" not in runner_text,
        "runner must not hard-code the development checkout path",
    )

    print("PASS: evidence taxonomy and manifest validated")
    print("PASS: unsupported performance claims remain NOT_MEASURED")
    print("PASS: evidence report sections and reproduction path validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
