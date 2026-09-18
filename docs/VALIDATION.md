# MERCURY X Validation

## Validation Philosophy

MERCURY X uses layered evidence. A focused unit test proves a small contract or invariant; integration tests prove handoffs; adversarial tests probe fail-closed behavior; executable certification evaluates required architecture gates; the full regression checks repository-wide compatibility.

Passing tests establish behavior in the tested software environment. They do not establish production deployment, real hardware performance, regulatory compliance, or empirical accuracy outside the evidence supplied.

## Test-Driven Development

Development follows **RED → GREEN → REFACTOR**:

1. **RED:** write a focused test that demonstrates the missing behavior or defect;
2. **GREEN:** implement the smallest change that satisfies the invariant;
3. **REFACTOR:** improve structure only while keeping the relevant focused and regression tests green.

Phase work is separated into reviewable checkpoints, with explicit boundaries intended to prevent later-phase behavior from leaking into earlier contracts.

## Focused Tests

Focused tests live under `tests/` and are organized by contract, engine, phase, or subsystem. Run the narrowest relevant file while developing:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_phase30_platform.py -q
```

## Integration and Adversarial Tests

Integration tests connect typed outputs across phase boundaries and verify identity, version, generation, fingerprint, provenance, authorization, and immutability. Failure-hardening tests cover malformed artifacts, stale state, contradictory evidence, cross-scope access, replay, double commit, unsafe promotion, and boundary leakage where relevant.

## Executable Certification Gates

Each phase has a manifest in `configs/certification/` and an evaluator in `src/mercury/certification/`. A certification gate executes repository checks and reports evidence. These gates are internal architecture/completeness checks, not third-party certifications.

Example:

```powershell
.\.venv\Scripts\python.exe -m mercury.certification.phase30
```

A valid certification must not silently skip required gates or hardcode a PASS result. Test files named `test_phase*_certification.py` exercise these evaluators.

## Full Regression

Use isolated temporary and cache directories on Windows:

```powershell
$stamp = Get-Date -Format "yyyyMMddHHmmss"
$bt = Join-Path $env:TEMP "mercury-pytest-$stamp"
$cache = Join-Path $env:TEMP "mercury-cache-$stamp"
.\.venv\Scripts\python.exe -m pytest tests -q --basetemp="$bt" -o cache_dir="$cache"
```

The repository reached **1506 passing tests** during final Phase 26–30 validation. That is a recorded repository regression result, not a benchmark or a claim about deployed infrastructure.

## Evidence Categories

| Category | Meaning | Appropriate claim |
|---|---|---|
| `MEASURED` | Observation from an executed command or named real system under a documented method | Only the recorded property, environment, command, and sample. |
| `SYNTHETIC` | Constructed fixtures or generated workloads rather than production traffic | The code handles the tested logical scenario. |
| `SIMULATED` | Output from a software model of a scheduler, topology, migration, counterfactual, or datacenter state | The control logic behaves as tested inside that simulation. |
| `STATIC_DEMO` | Maintained fixture rendered without live telemetry or control authority | The UI presents deterministic demonstration state. |
| `UNCALIBRATED` | Model output without empirical calibration evidence for predictive accuracy | Advisory behavior only; no accuracy claim. |
| `NOT_MEASURED` | No responsible empirical measurement exists in maintained evidence | No quantitative result may be inferred or estimated. |

Classifications can be combined: a locally executed test is `MEASURED` as a command outcome while its fixtures remain `SYNTHETIC`. Synthetic, simulated, static-demo, and uncalibrated evidence must not be relabeled as real infrastructure measurement. An interface for an empirical or learned backend does not prove that a calibrated model or trained artifact exists.

## Reproducible Evidence Surface

The maintained inventory and interpretation rules are in:

- [`evidence/EVIDENCE_MANIFEST.json`](evidence/EVIDENCE_MANIFEST.json);
- [`evidence/BENCHMARKS_AND_EVIDENCE.md`](evidence/BENCHMARKS_AND_EVIDENCE.md).

Validate them and generate a local snapshot from the repository root:

```powershell
.\.venv\Scripts\python.exe scripts\evidence\validate_evidence.py
.\.venv\Scripts\python.exe scripts\evidence\run_evidence.py
```

The generated `artifacts/evidence/mercury_evidence.json` is machine-specific, Git-ignored, and authoritative only for its recorded commit and environment. Command duration is reproducibility metadata, not a control-plane performance benchmark.

## Completion Criteria

A phase is considered internally complete when its scoped contracts and engines exist, focused and integration tests pass, required certification gates pass with evidence, compatibility is retained, and no unresolved in-scope safety blocker remains. This status does not imply operational readiness for production infrastructure.
