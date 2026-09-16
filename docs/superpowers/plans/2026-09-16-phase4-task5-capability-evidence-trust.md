# Phase 4 Task 5: Model Capability Evidence & Trust Baseline

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Categorically assess whether immutable evidence records sufficiently support one exact declared capability claim, without selecting models.

**Architecture:** Frozen evidence records retain claim linkage, source provenance, kind, explicit validity state, supporting/contradicting direction, and detail. A caller provides explicit hard trust requirements; the assessment preserves every evidence record and returns deterministic `ACCEPTABLE`, `INSUFFICIENT`, `CONFLICTING`, `STALE`, or `UNVERIFIED` status with nonblank issues.

**Tech Stack:** Python 3, Pydantic v2, pytest.

**Spec:** Locked Phase 4 Task 5 request, 2026-09-16.

## Global Constraints

- Create only this plan, `src/mercury/models/evidence.py`, and `tests/test_model_capability_evidence.py`.
- Keep evidence assessment separate from Task 1–4 compatibility and discovery semantics unless explicitly called later.
- Use categorical trust outcomes only; do not calculate model preference scores.
- Preserve stale, conflicting, negative, simulated, measured, observed, and declared evidence without promotion or deletion.
- Do not access the network or implement selection, placement, scheduling, or runtime behavior.

---

### Task 1: Immutable Capability Evidence Assessment

**Files:**
- Create: `src/mercury/models/evidence.py`
- Test: `tests/test_model_capability_evidence.py`

**Interfaces:**
- Consumes: caller-provided evidence records and assessment requirements.
- Produces: `CapabilityEvidence`, evidence kind/state enums, `CapabilityEvidenceAssessmentRequirements`, `CapabilityEvidenceIssue`, `CapabilityEvidenceAssessment`, and `assess_capability_evidence(evidence, requirements)`.

- [ ] **Step 1: Write failing evidence tests**

```python
assessment = assess_capability_evidence(
    (CapabilityEvidence(
        capability_claim="tool_use", source="provider manifest",
        source_revision="v1", reference_id="manifest/tool-use",
        detail="declares function calling", kind=CapabilityEvidenceKind.DECLARED,
        state=CapabilityEvidenceState.VALID, supports_claim=True,
    ),),
    CapabilityEvidenceAssessmentRequirements(capability_claim="tool_use"),
)
assert assessment.status is EvidenceAssessmentStatus.ACCEPTABLE
```

- [ ] **Step 2: Verify RED**

Run: `./.venv/Scripts/python.exe -m pytest tests/test_model_capability_evidence.py -q`

Expected: collection fails because `mercury.models.evidence` does not exist.

- [ ] **Step 3: Implement categorical assessment**

```python
def assess_capability_evidence(
    evidence: tuple[CapabilityEvidence, ...],
    requirements: CapabilityEvidenceAssessmentRequirements,
) -> CapabilityEvidenceAssessment:
    ...
```

Reject malformed or cross-claim evidence. Deterministically retain and order all records, detect valid positive/negative conflicts, retain stale/unverified categories, and enforce only caller-supplied requirements for evidence presence, current validity, measured/observed support, production evidence, simulated allowance, and conflict rejection.

- [ ] **Step 4: Verify GREEN**

Run: `./.venv/Scripts/python.exe -m pytest tests/test_model_capability_evidence.py -q`

Expected: all focused evidence tests pass.

- [ ] **Step 5: Run regression verification**

Run: `./.venv/Scripts/python.exe -m pytest tests -q`

Expected: the complete project suite passes with no changes outside Task 5.
