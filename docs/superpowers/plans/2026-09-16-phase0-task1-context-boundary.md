# Phase 0 Task 1: Context Artifact & Reuse Boundary Baseline Implementation Plan

> **For agentic workers:** Use a test-first RED → GREEN workflow. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish immutable, metadata-only context artifact references and a deterministic fail-closed reuse gate for Phase 0 cognitive infrastructure.

**Architecture:** `models.py` defines versioned, strict `ContractModel` boundaries with only metadata and opaque storage references; it stores no payload-bearing maps or mutable collections. `reuse_gate.py` evaluates authorization, privacy, integrity, and portability-specific compatibility in a fixed order, returning a reason-bearing decision rather than moving, caching, scheduling, or optimizing context.

**Tech Stack:** Python 3.13, Pydantic v2, pytest.

**Spec:** Locked Phase 0 Task 1 specification supplied by the user on 2026-09-16; no separate repository spec file exists.

## Global Constraints

- Touch only `src/mercury/context/models.py`, `src/mercury/context/reuse_gate.py`, `tests/test_context_boundary.py`, and this plan document.
- Preserve every certified contract and do not modify `src/mercury/context/__init__.py`.
- Context artifacts are metadata/reference records only: raw prompts, raw context, API keys, tokens, credentials, and payload fields are forbidden by strict contracts.
- Reuse is fail-closed; locality or cache benefit cannot override authorization, privacy, or integrity.
- Do not implement session-memory fabric, global context memory, prediction, semantic KV cache, GPU/cache movement, scheduling optimization, or learning.
- Start with failing tests, run focused tests after implementation, then run the full project-local suite exactly once.

---

### Task 1: Context artifact contracts and deterministic reuse gate

**Files:**

- Create: `src/mercury/context/models.py`
- Create: `src/mercury/context/reuse_gate.py`
- Create: `tests/test_context_boundary.py`
- Modify: `docs/superpowers/plans/2026-09-16-phase0-task1-context-boundary.md`

**Interfaces:**

- Produces `ContextArtifactKind` with exactly `INPUT_CONTEXT`, `SESSION_CONTEXT`, `RETRIEVAL_CONTEXT`, `MODEL_STATE`, `KV_STATE`, `TOOL_STATE`, `EXECUTION_STATE`, `INTERMEDIATE_RESULT`, `CHECKPOINT`, and `SHARED_ARTIFACT`.
- Produces `ContextPortability` with exactly `PORTABLE`, `MODEL_SPECIFIC`, and `RUNTIME_SPECIFIC`.
- Produces `ContextStorageTier` with `ACCELERATOR_MEMORY`, `SYSTEM_RAM`, `LOCAL_NVME`, `DISTRIBUTED_CACHE`, `OBJECT_STORAGE`, and `ARCHIVE`, mirroring the Master Spec context hierarchy.
- Produces immutable `ContextArtifact`, `ContextReuseRequest`, and `ContextReuseDecision` contracts. Collections are tuples, so Pydantic validation cannot leave mutable authorization or reason lists exposed.
- Produces `ContextReuseGate.evaluate(artifact, request) -> ContextReuseDecision`.

- [ ] **Step 1: Write failing contract and gate tests**

Create `tests/test_context_boundary.py` with literal fixtures and behavior assertions for:

```python
def test_valid_portable_reuse_is_allowed():
    decision = ContextReuseGate().evaluate(portable_artifact, authorized_request)
    assert decision.allowed is True
    assert decision.reasons == ("reuse requirements satisfied",)

def test_unauthorized_or_privacy_incompatible_reuse_is_denied():
    owner_decision = ContextReuseGate().evaluate(portable_artifact, unauthorized_request)
    privacy_decision = ContextReuseGate().evaluate(portable_artifact, privacy_mismatch_request)
    assert "owner is not authorized" in owner_decision.reasons
    assert "privacy level is incompatible" in privacy_decision.reasons

def test_reuse_gate_fails_closed_for_integrity_and_portability_compatibility():
    assert ContextReuseGate().evaluate(missing_integrity_artifact, request).allowed is False
    assert ContextReuseGate().evaluate(model_specific_artifact, wrong_model_request).allowed is False
    assert ContextReuseGate().evaluate(runtime_specific_artifact, wrong_runtime_request).allowed is False
```

Also assert that extra `payload`, `api_key`, `token`, and `credentials` fields are rejected, a portable artifact stays `PORTABLE`, tuple-backed fields cannot be mutated in place, and every allow/deny decision has an explicit non-empty reason.

- [ ] **Step 2: Run the focused test to prove RED**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_context_boundary.py -v
```

Expected: collection or import failure because `mercury.context.models` and `mercury.context.reuse_gate` do not yet exist.

- [ ] **Step 3: Add the metadata/reference-only contracts**

Create `models.py` using `mercury.contracts.base.ContractModel`, `str`-backed enums, and these contract fields:

```python
class ContextArtifact(ContractModel):
    schema_version: Literal["mercury.context.artifact/v1"] = "mercury.context.artifact/v1"
    artifact_id: str
    owner_id: str
    tenant_id: str
    authorized_owner_ids: tuple[str, ...]
    authorized_tenant_ids: tuple[str, ...]
    kind: ContextArtifactKind
    portability: ContextPortability
    storage_tier: ContextStorageTier
    privacy_level: str
    reference_uri: str
    integrity_evidence: str | None = None
    model_id: str | None = None
    runtime_id: str | None = None
```

Require non-empty identifiers and privacy labels. Validate `reference_uri` as an opaque, credential-free URI with no query, fragment, whitespace, or embedded user credentials. Keep authorization and decision collections as tuples; do not introduce general-purpose metadata or payload dictionaries.

- [ ] **Step 4: Implement the deterministic gate**

Create `reuse_gate.py` with a fixed check order: artifact reference, authorized owner, authorized tenant, exact privacy compatibility, integrity-evidence format, model compatibility for `MODEL_SPECIFIC`, and runtime compatibility for `RUNTIME_SPECIFIC`.

```python
class ContextReuseGate:
    def evaluate(
        self,
        artifact: ContextArtifact,
        request: ContextReuseRequest,
    ) -> ContextReuseDecision:
        reasons: list[str] = []
        if request.artifact_id != artifact.artifact_id:
            reasons.append("artifact reference does not match")
        if request.requester_owner_id not in artifact.authorized_owner_ids:
            reasons.append("owner is not authorized")
        if request.requester_tenant_id not in artifact.authorized_tenant_ids:
            reasons.append("tenant is not authorized")
        if request.privacy_level != artifact.privacy_level:
            reasons.append("privacy level is incompatible")
        if not _SHA256_EVIDENCE.fullmatch(artifact.integrity_evidence or ""):
            reasons.append("integrity evidence is missing or invalid")
        if artifact.portability is ContextPortability.MODEL_SPECIFIC and request.model_id != artifact.model_id:
            reasons.append("model compatibility mismatch")
        if artifact.portability is ContextPortability.RUNTIME_SPECIFIC and request.runtime_id != artifact.runtime_id:
            reasons.append("runtime compatibility mismatch")
        return ContextReuseDecision(
            artifact_id=artifact.artifact_id,
            allowed=not reasons,
            reasons=tuple(reasons) or ("reuse requirements satisfied",),
        )
```

Treat an integrity value as valid only when it is `sha256:` followed by 64 lowercase hexadecimal characters. Return `allowed=False` with every applicable reason when any hard requirement fails; return `allowed=True` with `("reuse requirements satisfied",)` only when all hard requirements pass.

- [ ] **Step 5: Run focused tests to prove GREEN**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_context_boundary.py -v
```

Expected: all context-boundary regressions pass, including locality-benefit denial cases and post-validation mutation rejection.

- [ ] **Step 6: Perform the scoped hygiene check**

Confirm only the four allowed Task 1 paths are modified and inspect the test names against the locked regression list. Update this plan's completed checkboxes with the actual command outcomes.

- [ ] **Step 7: Run the complete regression suite exactly once**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -v
```

Expected: the existing certified suite plus `tests/test_context_boundary.py` pass together. Stop after reporting the exact total; do not begin Task 2.
