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
| Synthetic | Constructed fixtures used to exercise contracts and boundary conditions | The code handles the tested logical scenario. |
| Simulated | Output from a model of a scheduler, topology, migration, counterfactual, or datacenter state | The control logic behaves as tested inside that simulation. |
| Measured | Observation captured from a named real system under a documented method | Only the measured property, environment, and sample may be claimed. |
| Calibrated | A model linked to explicit calibration artifacts/data and a supported operating domain | Accuracy claims remain limited to that evidence and domain. |

Synthetic and simulated evidence must not be relabeled as measured. An interface for an empirical or learned backend does not prove that a calibrated model or trained artifact exists.

## Completion Criteria

A phase is considered internally complete when its scoped contracts and engines exist, focused and integration tests pass, required certification gates pass with evidence, compatibility is retained, and no unresolved in-scope safety blocker remains. This status does not imply operational readiness for production infrastructure.

