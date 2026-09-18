"""Run reproducible local MERCURY X evidence checks and emit JSON."""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import subprocess
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "artifacts" / "evidence" / "mercury_evidence.json"
SNAPSHOT_SCHEMA = "mercury.evidence-snapshot/v1"


def _run(
    check_id: str,
    command: Sequence[str],
    classifications: Sequence[str],
    *,
    cwd: Path = ROOT,
) -> dict[str, Any]:
    started = time.perf_counter()
    completed = subprocess.run(
        list(command),
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    duration = round(time.perf_counter() - started, 3)
    combined = "\n".join(part.strip() for part in (completed.stdout, completed.stderr) if part.strip())
    summary_lines = combined.splitlines()[-20:]
    passed_match = re.search(r"(?P<count>\d+) passed", combined)
    return {
        "id": check_id,
        "command": list(command),
        "classifications": list(classifications),
        "outcome": "PASS" if completed.returncode == 0 else "FAIL",
        "exit_code": completed.returncode,
        "duration_seconds": duration,
        "test_count": int(passed_match.group("count")) if passed_match else None,
        "output_tail": summary_lines,
    }


def _skipped(check_id: str, classifications: Sequence[str], reason: str) -> dict[str, Any]:
    return {
        "id": check_id,
        "command": [],
        "classifications": list(classifications),
        "outcome": "NOT_RUN",
        "exit_code": None,
        "duration_seconds": None,
        "test_count": None,
        "output_tail": [reason],
    }


def _git(*args: str) -> str:
    completed = subprocess.run(
        ["git", "-c", f"safe.directory={ROOT.as_posix()}", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return completed.stdout.strip()


def _certification_test_files() -> list[str]:
    tests = ROOT / "tests"
    selected = {
        tests / "test_certification_framework.py",
        tests / "test_phase0_integration.py",
        *tests.glob("test_phase*_certification.py"),
        *tests.glob("test_phase*_certification_manifests.py"),
    }
    return [str(path.relative_to(ROOT)) for path in sorted(selected)]


def _inventory() -> dict[str, Any]:
    expected_phases = list(range(31))
    missing_manifests = [
        phase
        for phase in expected_phases
        if not (ROOT / "configs" / "certification" / f"phase{phase}.json").is_file()
    ]
    missing_evaluators = [
        phase
        for phase in expected_phases
        if not (ROOT / "src" / "mercury" / "certification" / f"phase{phase}.py").is_file()
    ]
    return {
        "phase_range": "0-30",
        "expected_phase_count": 31,
        "missing_manifests": missing_manifests,
        "missing_evaluators": missing_evaluators,
        "status": "PASS" if not missing_manifests and not missing_evaluators else "FAIL",
        "classification": "SYNTHETIC",
        "claim_boundary": "Repository artifact coverage only; not third-party certification.",
    }


def build_snapshot(*, include_python_tests: bool) -> dict[str, Any]:
    python = sys.executable
    npm = "npm.cmd" if os.name == "nt" else "npm"
    checks: list[dict[str, Any]] = []

    certification_files = _certification_test_files()
    checks.append(
        _run(
            "certification_tests",
            [python, "-m", "pytest", *certification_files, "-q"],
            ["MEASURED", "SYNTHETIC"],
        )
    )
    checks.append(
        _run(
            "phase30_certification_cli",
            [python, "-m", "mercury.certification.phase30"],
            ["MEASURED", "SYNTHETIC"],
        )
    )
    checks.append(
        _run(
            "control_center_validation",
            [npm, "run", "check"],
            ["MEASURED", "STATIC_DEMO", "SYNTHETIC"],
            cwd=ROOT / "ui" / "control-center",
        )
    )
    checks.append(
        _run(
            "scenario_validation",
            [npm, "run", "check:scenarios"],
            ["MEASURED", "STATIC_DEMO", "SYNTHETIC", "SIMULATED"],
            cwd=ROOT / "ui" / "control-center",
        )
    )

    if include_python_tests:
        stamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        temp_root = Path(tempfile.gettempdir())
        base_temp = temp_root / f"mercury-pytest-{stamp}"
        cache = temp_root / f"mercury-cache-{stamp}"
        checks.append(
            _run(
                "python_full_regression",
                [
                    python,
                    "-m",
                    "pytest",
                    "tests",
                    "-q",
                    f"--basetemp={base_temp}",
                    "-o",
                    f"cache_dir={cache}",
                ],
                ["MEASURED", "SYNTHETIC"],
            )
        )
    else:
        checks.append(
            _skipped(
                "python_full_regression",
                ["NOT_MEASURED"],
                "Skipped by --skip-python-tests; no current regression claim is emitted.",
            )
        )

    inventory = _inventory()
    failed_checks = [check["id"] for check in checks if check["outcome"] == "FAIL"]
    if inventory["status"] == "FAIL":
        failed_checks.append("certification_inventory")
    return {
        "schema_version": SNAPSHOT_SCHEMA,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "git": {
            "commit": _git("rev-parse", "HEAD"),
            "dirty": bool(_git("status", "--short", "--untracked-files=all")),
        },
        "environment": {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "architecture": platform.machine(),
            "python": platform.python_version(),
            "node": _run("node_version", ["node", "--version"], ["MEASURED"])["output_tail"],
            "npm": _run("npm_version", [npm, "--version"], ["MEASURED"])["output_tail"],
        },
        "certification_inventory": inventory,
        "checks": checks,
        "summary": {
            "overall_status": "PASS" if not failed_checks else "FAIL",
            "passed": sum(check["outcome"] == "PASS" for check in checks),
            "failed": sum(check["outcome"] == "FAIL" for check in checks),
            "not_run": sum(check["outcome"] == "NOT_RUN" for check in checks),
            "failed_check_ids": failed_checks,
        },
        "claim_boundary": (
            "Local control-plane validation only. It does not measure accelerator, cloud, network, "
            "production scheduler, model-quality, migration-downtime, or datacenter performance."
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--skip-python-tests",
        action="store_true",
        help="Run evidence and certification checks without claiming a current full regression result.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = args.output if args.output.is_absolute() else ROOT / args.output
    snapshot = build_snapshot(include_python_tests=not args.skip_python_tests)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Evidence snapshot: {output}")
    print(f"Overall status: {snapshot['summary']['overall_status']}")
    for check in snapshot["checks"]:
        print(f"{check['id']}: {check['outcome']}")
    return 0 if snapshot["summary"]["overall_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
