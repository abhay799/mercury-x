# Phase 5 Dynamic Model Composition Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement and certify a deterministic, immutable Phase 5 fabric that produces zero, one, or many bounded logical model-composition candidates from certified Phase 2–4 inputs.

**Architecture:** Phase 5 is a one-way pipeline under `src/mercury/composition/`: frozen contracts, a seven-shape certified pattern library, deterministic exact-record instantiation, independent candidate validation, and provenance-preserving bounded generation. Candidate order is canonical only; no component ranks, scores, selects, assigns Phase 3 graph nodes, chooses hardware, places, schedules, optimizes, or invokes models.

**Tech Stack:** Python 3.13, frozen dataclasses and existing Pydantic `ContractModel` conventions, SHA-256 canonical identifiers, JSON certification configuration, pytest.

**Spec:** `docs/superpowers/specs/2026-09-17-phase5-dynamic-model-composition-design.md`

## Global Constraints

- The public schema is exactly `mercury.model-composition/v1`.
- The only roles are `PRIMARY`, `SPECIALIST`, `VERIFIER`, `CRITIC`, `RETRIEVAL_AUGMENTER`, and `TOOL_MODEL`.
- The certified pattern library contains exactly seven topology shapes: `SINGLE`, `PRIMARY -> VERIFIER`, `PRIMARY -> CRITIC`, `PRIMARY -> SPECIALIST -> PRIMARY`, `PRIMARY -> RETRIEVAL_AUGMENTER -> PRIMARY`, `PRIMARY -> TOOL_MODEL -> PRIMARY`, and `PRIMARY -> SPECIALIST -> VERIFIER`.
- `MAX_COMPOSITION_NODES = 3` and `MAX_COMPOSITION_CANDIDATES = 256` are hard certified maxima. Callers may request smaller positive limits only.
- All public contracts and nested collections are immutable. No operation mutates Phase 2 profiles, Phase 3 graphs/readiness, Phase 4 records/registries/results/evidence, patterns, drafts, candidates, or results.
- Composition IDs are deterministic SHA-256 identifiers derived from canonical semantic content. Random UUIDs, wall-clock time, Python `hash()`, filesystem paths, environment values, and unordered iteration are forbidden decision inputs.
- Canonical ordering exists only for reproducibility. It must never encode or be described as preference, suitability, quality, cost, latency, fallback, or execution order.
- Zero, one, or many valid candidates are supported. Each candidate is validated independently; rejected candidates remain immutable and retain complete deterministic reasons and provenance.
- Repeated `PRIMARY` stages in return topologies use the same exact provider, model ID, family, and revision.
- Truncation metadata is explicit and includes configured bounds, emitted counts, completion/truncation state, canonical order description, nonblank truncation reason, and a lower bound of at least `cap + 1` when truncated.
- Phase 5 preserves Phase 2 request/workload/session identity, Phase 3 graph identity and provenance, the Phase 4 registry fingerprint, exact model identity/revision, compatibility/discovery results, and explicitly required evidence assessments.
- Malformed, failed, identity-inconsistent, provenance-incomplete, or non-ready upstream state fails closed before or during candidate generation.
- Capability checks reuse Phase 4 `evaluate_compatibility`, `discover_capabilities`, and `assess_capability_evidence`; no capability is inferred from a model name, provider name, family, free-form user wording, or node-purpose keywords.
- Composition graphs are bounded logical DAGs. Cycles, recursion, self-calling loops, self-edges, orphan stages, disconnected stages, unsupported role transitions, open-ended swarms, and free-form topology generation are forbidden.
- Phase 5 performs no ranking, scoring, winner selection, Phase 3 graph-node assignment, fallback ordering, model composition outside certified templates, hardware matching, placement, scheduling, cost/latency/quality optimization, or runtime invocation.
- Each implementation task begins with focused RED tests, reaches focused GREEN, runs the full regression suite exactly once only after focused GREEN, creates one scoped Git checkpoint, and stops before the next task.

## Shared Canonical Mappings

The implementation uses explicit mappings rather than text inference:

- Phase 2 `TEXT`, `IMAGE`, `AUDIO`, `VIDEO`, and `STRUCTURED_DATA` map to the same-valued Phase 4 `ModelModality`; `MULTIMODAL` expands only from `WorkloadSignals.explicit_modalities`; `CODE` requires explicit Phase 4 code capability flags and a text or structured-data contract as declared by the graph.
- `ComputationalCapability.REASONING` requires `ReasoningCapability.GENERAL`; `HIGH` or `DEEP` reasoning additionally requires `ReasoningCapability.MULTI_STEP`.
- `RETRIEVAL` requires `supports_retrieval`.
- `VISION` requires the exact image/video input modality carried by the workload or graph.
- `SPEECH` requires the exact audio input/output modality carried by the workload or graph.
- `STRUCTURED_OUTPUT` requires both `supports_json_output` and `supports_schema_constrained_output` when schema-constrained output is explicit.
- `TOOL_USE` requires `supports_tool_use`; structured argument/result handoffs additionally require `supports_structured_tool_arguments` and `supports_tool_result_consumption`.
- Logical `CODE_EXECUTION` is represented only as a `TOOL_MODEL` handoff requiring tool use, structured arguments, tool-result consumption, code understanding, and the graph's exact code input/output contract. Phase 5 never claims that a model executes code itself.
- `GENERATION` is satisfied by the exact declared output modality; Phase 5 does not invent a separate unsupported generation flag.

An input requirement that cannot be represented exactly with certified Phase 4 fields produces no compatible binding and a deterministic fail-closed issue.

---

## Task 1: Composition Contract Baseline

**Files:**

- Create: `src/mercury/composition/contracts.py`
- Create: `tests/test_composition_contracts.py`
- Modify: none

**Interfaces consumed:**

- `mercury.contracts.base.ContractModel`
- `mercury.graph.models.GraphDependencyType`
- `mercury.models.capabilities.ModelCapabilityRecord`
- `mercury.models.capabilities.ModelModality`
- `mercury.models.compatibility.ModelCapabilityRequirements`
- `mercury.models.evidence.CapabilityEvidenceAssessment`

**Frozen public interfaces produced:**

- `COMPOSITION_SCHEMA_VERSION: Literal["mercury.model-composition/v1"]`
- `MAX_COMPOSITION_NODES = 3`
- `MAX_COMPOSITION_CANDIDATES = 256`
- `CompositionRole(str, Enum)` with exactly the six locked roles
- `CertifiedTopology(str, Enum)` with exactly the seven locked shapes
- `CompositionValidity(str, Enum)` with `VALID` and `REJECTED`
- `CompositionResultStatus(str, Enum)` with `READY`, `NOT_APPLICABLE`, and `FAIL`
- `CompositionProvenanceReference(ContractModel)` with `source_phase`, `artifact_id`, and nonblank `evidence`
- `CompositionArtifactContract(ContractModel)` with `artifact_id`, deterministic `modalities`, `requires_structured_output`, and nonblank `evidence`
- `CapabilityJustification(ContractModel)` with `requirement_id`, `capability_field`, `declared_value`, and nonblank `reason`
- `CompositionNode(ContractModel)` with `stage_id`, `role`, exact `model_record`, hard `requirements`, input/output artifact contracts, justifications, and provenance
- `CompositionEdge(ContractModel)` with source/target stage IDs, `GraphDependencyType`, `artifact_id`, and nonblank evidence
- `CompositionCandidateDraft(ContractModel)` with schema/identity fields, `composition_id`, `topology`, nodes, edges, satisfied requirement IDs, evidence assessments, and provenance
- `CompositionRejection(ContractModel)` with `issue_id`, optional stage/edge reference, violated invariant, and nonblank reason
- `CompositionCandidate(CompositionCandidateDraft)` adding `validity` and deterministic `rejection_reasons`
- `CompositionGenerationPolicy(ContractModel)` with positive `max_nodes` and `max_candidates` bounded by 3 and 256
- `CompositionGenerationMetadata(ContractModel)` with configured caps, valid/rejected counts, `enumeration_complete`, `truncated`, optional truncation reason, candidate lower bound, and canonical-order description
- `CompositionResult(ContractModel)` with status, valid candidates, rejected candidates, generation metadata, and deterministic result issues
- `canonical_model_identity(record: ModelCapabilityRecord) -> tuple[str, str, str, str]`

Contract validation must normalize tuple collections deterministically, reject blank identities/evidence, reject duplicate stage IDs, dangling edges, self-edges, cycles, orphan stages, more than three nodes, malformed model records, identity drift, mutable nested input, unsupported enum values, inconsistent validity/rejection state, and forbidden decision fields. `VALID` candidates have no rejection reasons; `REJECTED` candidates have at least one. The contract layer validates DAG safety but does not decide certified pattern conformance or candidate suitability.

- [ ] **Step 1: Write focused contract tests**

Create tests for minimal `SINGLE`, every role/topology enum, a valid three-stage draft, exact identity/revision preservation, immutable nested tuples, deterministic equality/serialization, validity/rejection consistency, node and candidate caps, cycle/self-edge/dangling/orphan rejection, and forbidden ranking/selection/hardware/runtime fields.

Representative RED test:

```python
def test_valid_single_candidate_draft_is_frozen() -> None:
    draft = CompositionCandidateDraft(
        schema_version="mercury.model-composition/v1",
        composition_id="sha256:" + "a" * 64,
        request_id="request-1",
        workload_id="workload-1",
        session_id="session-1",
        graph_id="graph-1",
        topology=CertifiedTopology.SINGLE,
        nodes=(primary_node(),),
        edges=(),
        satisfied_requirement_ids=("generation",),
        evidence_assessments=(),
        provenance=(provenance("phase4", "registry-1"),),
    )
    assert draft.nodes[0].role is CompositionRole.PRIMARY
    with pytest.raises(ValidationError):
        draft.composition_id = "changed"
```

- [ ] **Step 2: Run RED verification**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_composition_contracts.py -q
```

Expected failure: test collection raises `ModuleNotFoundError: No module named 'mercury.composition.contracts'`.

- [ ] **Step 3: Implement the minimal frozen contracts**

Create the enums, constants, frozen Pydantic contracts, canonical tuple normalization, exact identity helper, bounded integer validators, DAG validation, validity/rejection cross-field validation, result-status invariants, and deterministic `model_dump(mode="json")` behavior required by the focused tests. Do not add pattern instances, instantiation, validation policy, or generation logic.

- [ ] **Step 4: Run focused GREEN verification**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_composition_contracts.py -q
```

Expected result: all Task 1 focused tests pass with no warning or collection error.

- [ ] **Step 5: Run the full regression once**

Run only after focused GREEN:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

Expected result: the existing 756-test baseline plus Task 1 tests passes.

- [ ] **Step 6: Create the Task 1 checkpoint**

Stage only `src/mercury/composition/contracts.py` and `tests/test_composition_contracts.py`, verify the staged file list, and commit:

```powershell
git commit -m "feat: add Phase 5 composition contract baseline"
```

**STOP boundary:** Stop after reporting focused/full results, committed files, commit hash, final Git status, and blockers. Do not begin Task 2.

---

## Task 2: Certified Pattern Library

**Files:**

- Create: `src/mercury/composition/patterns.py`
- Create: `tests/test_composition_patterns.py`
- Modify: none

**Interfaces consumed:**

- `CompositionRole`, `CertifiedTopology`, and `MAX_COMPOSITION_NODES` from `mercury.composition.contracts`
- `GraphDependencyType` from `mercury.graph.models`

**Frozen public interfaces produced:**

- `PatternApplicability(str, Enum)` with `SINGLE_CAPABLE`, `VERIFICATION_REQUIRED`, `CRITIQUE_REQUIRED`, `SPECIALIST_RETURN_REQUIRED`, `RETRIEVAL_RETURN_REQUIRED`, `TOOL_RETURN_REQUIRED`, and `SPECIALIST_VERIFICATION_REQUIRED`
- `PatternSlot(ContractModel)` with `stage_id`, `role`, and optional `identity_group`
- `PatternEdge(ContractModel)` with source/target stage IDs and `GraphDependencyType`
- `CertifiedCompositionPattern(ContractModel)` with topology, stable `pattern_id`, applicability, slots, edges, and `max_nodes`
- `CERTIFIED_PATTERNS: tuple[CertifiedCompositionPattern, ...]`
- `get_certified_patterns() -> tuple[CertifiedCompositionPattern, ...]`
- `get_certified_pattern(topology: CertifiedTopology) -> CertifiedCompositionPattern`

The library must encode exactly seven shapes and no extension hook for free-form patterns. Return-pattern primary slots use distinct stage IDs and the same `identity_group="primary"`. Pattern construction rejects unknown roles, unsupported transitions, duplicate/dangling/self edges, cycles, orphans, disconnected paths, recursive shapes, and any pattern over three nodes. Enumeration follows `CertifiedTopology` declaration order only.

- [ ] **Step 1: Write focused pattern tests**

Create one structural assertion for each locked shape, assert the exact count is seven, verify repeated-primary identity groups, deterministic retrieval, frozen collections, no cycles/recursion/orphans, and rejection of any eighth or malformed shape.

Representative RED test:

```python
def test_certified_library_contains_exactly_seven_locked_shapes() -> None:
    patterns = get_certified_patterns()
    assert tuple(pattern.topology for pattern in patterns) == tuple(CertifiedTopology)
    assert len(patterns) == 7
    assert all(len(pattern.slots) <= MAX_COMPOSITION_NODES for pattern in patterns)
```

- [ ] **Step 2: Run RED verification**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_composition_patterns.py -q
```

Expected failure: test collection raises `ModuleNotFoundError: No module named 'mercury.composition.patterns'`.

- [ ] **Step 3: Implement the minimal certified library**

Define the three frozen pattern contracts, validate their DAG and transition invariants, instantiate exactly the seven locked patterns, apply the `primary` identity group to repeated primary stages, and expose exact lookup plus canonical tuple enumeration. Do not evaluate workload applicability or bind models.

- [ ] **Step 4: Run focused GREEN verification**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_composition_patterns.py -q
```

Expected result: all Task 2 focused tests pass.

- [ ] **Step 5: Run the full regression once**

Run only after focused GREEN:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

Expected result: the complete suite passes once from the final Task 2 state.

- [ ] **Step 6: Create the Task 2 checkpoint**

Stage only `src/mercury/composition/patterns.py` and `tests/test_composition_patterns.py`, verify the staged file list, and commit:

```powershell
git commit -m "feat: add Phase 5 certified composition patterns"
```

**STOP boundary:** Stop after Task 2 reporting. Do not begin Task 3.

---

## Task 3: Candidate Instantiation Engine

**Files:**

- Create: `src/mercury/composition/instantiation.py`
- Create: `tests/test_composition_instantiation.py`
- Modify: none

**Interfaces consumed:**

- `WorkloadIntelligencePipelineResult`, `PipelineStatus`, and contained Phase 2 profile/signals/provenance from `mercury.intelligence.pipeline`
- `ExecutionGraph`, `ExecutionGraphNode`, `GraphNodeType`, and `GraphDependencyType` from `mercury.graph.models`
- `GraphReadinessResult` and `GraphReadinessStatus` from `mercury.graph.readiness`
- `ModelCapabilityRegistry` from `mercury.models.registry`
- `ModelCapabilityRequirements` from `mercury.models.compatibility`
- `CapabilityDiscoveryQuery`, `CapabilityDiscoveryResult`, and `discover_capabilities` from `mercury.models.discovery`
- `CapabilityEvidence`, `CapabilityEvidenceAssessmentRequirements`, `CapabilityEvidenceAssessment`, and `assess_capability_evidence` from `mercury.models.evidence`
- Task 1 draft/node/edge/provenance contracts and canonical identity helper
- Task 2 certified pattern contracts and `get_certified_patterns`

**Frozen public interfaces produced:**

- `CompositionRoleRequirement(ContractModel)` with role, stable requirement IDs, one `ModelCapabilityRequirements`, artifact input/output contracts, and provenance
- `CompositionEvidenceConstraint(ContractModel)` with role, exact capability claim, assessment requirements, and immutable evidence records
- `CompositionInstantiationRequest(ContractModel)` with intelligence result, graph, readiness result, registry, explicit role requirements, explicit evidence constraints, and `composition_required`
- `InstantiationIssue(ContractModel)` with `issue_id`, affected role/pattern, and nonblank reason
- `CompositionInstantiationResult(ContractModel)` with canonical draft tuple, applicable topology tuple, evidence assessments, and deterministic issues
- `derive_role_requirements(request: CompositionInstantiationRequest, pattern: CertifiedCompositionPattern) -> tuple[CompositionRoleRequirement, ...]`
- `iter_composition_candidate_drafts(request: CompositionInstantiationRequest) -> Iterator[CompositionCandidateDraft]`
- `instantiate_composition_candidates(request: CompositionInstantiationRequest) -> CompositionInstantiationResult`

`CompositionInstantiationRequest` validates Phase 2 status is not `FAIL`, Phase 3 readiness is `READY`, graph/readiness/intelligence identities agree, the graph retains required provenance, the registry is valid, role/evidence requirements are immutable and nonblank, and explicit role requirements refer only to locked roles. `CRITIC` and other roles that cannot be derived from current graph enums are eligible only through explicit canonical `CompositionRoleRequirement` input with provenance; node-purpose text is never parsed.

Pattern applicability uses explicit graph types and role requirements: `VALIDATION` enables verifier patterns, explicit critic requirements enable critic patterns, specialist requirements enable specialist patterns, `RETRIEVAL` enables the retrieval-return pattern, and `TOOL` enables the tool-return pattern. `SINGLE` is applicable only when one exact record can satisfy the complete primary requirement set. The shared canonical mappings in this plan define capability translation.

Per role, construct a `CapabilityDiscoveryQuery` and call `discover_capabilities`; do not reproduce compatibility logic. Assess evidence only for supplied `CompositionEvidenceConstraint` values and attach the exact assessment to the draft. Evidence that is not explicitly required is preserved when supplied but cannot create a new hard constraint. Role binding enumeration is finite and canonical by pattern order, slot order, and exact model identity. Repeated identity groups bind one exact record to every grouped slot.

`composition_id` is `sha256:` plus the digest of canonical JSON containing schema version, request/workload/session/graph IDs, topology, ordered stage roles and exact model identities, canonical edges, and assigned hard requirements. Provenance is excluded from the semantic ID but retained in the draft so equivalent semantic drafts can merge provenance later.

- [ ] **Step 1: Write focused instantiation tests**

Test valid `SINGLE`; each explicit topology applicability rule; zero/one/many drafts; exact identity/revision propagation; same-primary return binding; Phase 4 discovery/evidence reuse; deterministic IDs/order; unsupported hard requirement returning issues/no binding; malformed/failed/not-ready/mismatched upstream rejection; no raw-text or model-name inference; no input mutation; and no ranking/selection fields.

Representative RED test:

```python
def test_identical_inputs_produce_identical_single_draft_id() -> None:
    request = valid_instantiation_request()
    first = instantiate_composition_candidates(request)
    second = instantiate_composition_candidates(request)
    assert first == second
    assert first.drafts[0].composition_id.startswith("sha256:")
    assert first.drafts[0].nodes[0].model_record is request.registry.records[0]
```

- [ ] **Step 2: Run RED verification**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_composition_instantiation.py -q
```

Expected failure: test collection raises `ModuleNotFoundError: No module named 'mercury.composition.instantiation'`.

- [ ] **Step 3: Implement deterministic rule-based instantiation**

Add strict input validation, exact capability mapping, role requirement derivation, pattern applicability, Phase 4 discovery calls, explicit evidence assessment calls, canonical finite Cartesian binding iteration, repeated identity-group enforcement, deterministic node/edge construction, SHA-256 composition IDs, provenance linkage, and fail-closed issues. Do not validate final candidate status, deduplicate drafts, cap enumeration, or expose preferred ordering.

- [ ] **Step 4: Run focused GREEN verification**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_composition_instantiation.py -q
```

Expected result: all Task 3 focused tests pass.

- [ ] **Step 5: Run the full regression once**

Run only after focused GREEN:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

Expected result: the complete suite passes once from the final Task 3 state.

- [ ] **Step 6: Create the Task 3 checkpoint**

Stage only `src/mercury/composition/instantiation.py` and `tests/test_composition_instantiation.py`, verify the staged file list, and commit:

```powershell
git commit -m "feat: add Phase 5 candidate instantiation baseline"
```

**STOP boundary:** Stop after Task 3 reporting. Do not begin Task 4.

---

## Task 4: Composition Validation Engine

**Files:**

- Create: `src/mercury/composition/validation.py`
- Create: `tests/test_composition_validation.py`
- Modify: none

**Interfaces consumed:**

- `WorkloadIntelligencePipelineResult`
- `ExecutionGraph` and `GraphDependencyType`
- `GraphReadinessResult` and `GraphReadinessStatus`
- `ModelCapabilityRegistry`
- `evaluate_compatibility` and `CompatibilityStatus`
- `CapabilityEvidenceAssessment` and `EvidenceAssessmentStatus`
- Task 1 contracts and exact identity helper
- Task 2 certified pattern lookup

**Frozen public interfaces produced:**

- `CompositionValidationStatus(str, Enum)` with `PASS` and `FAIL`
- `CompositionValidationIssue(ContractModel)` with stable `issue_id`, optional stage/edge, violated field, and nonblank reason
- `CompositionValidationContext(ContractModel)` with intelligence result, graph, readiness result, registry, and complete hard requirement IDs
- `CompositionValidationResult(ContractModel)` with status, immutable final `CompositionCandidate`, deterministic issues, and checked invariant IDs
- `validate_composition_candidate(draft: CompositionCandidateDraft, context: CompositionValidationContext) -> CompositionValidationResult`

Validation is read-only and never repairs drafts. It recomputes the draft's canonical composition ID; verifies upstream and candidate identity; verifies every exact model record exists unchanged in the registry; verifies exact certified pattern shape, repeated-primary identity, unique stages, edges, DAG reachability, and node bound; reruns Phase 4 compatibility for each stage requirement; validates whole-candidate requirement coverage; checks source output and target input artifact contracts for every handoff; requires `ACCEPTABLE` evidence only where the draft carries an explicit hard evidence requirement; verifies provenance completeness; and recursively rejects boundary-leaking fields or metadata.

The result converts all issues into sorted `CompositionRejection` values. No issues yields a `VALID` candidate and `PASS`; any issue yields a `REJECTED` candidate and `FAIL`. Validation of one draft has no effect on any other draft.

- [ ] **Step 1: Write focused validation tests**

Test every certified topology passing; malformed structure; wrong pattern shape; dangling/self/cyclic/orphan flow; unsupported transition; repeated-primary identity drift; missing registry record; exact revision mismatch; missing capability; missing hard requirement coverage; invalid structured/tool/retrieval handoff; unacceptable explicitly required evidence; absent non-required evidence remaining nonblocking; provenance loss; deterministic issue/rejection order; stale composition ID; nested phase-boundary leakage; source immutability; and result immutability.

Representative RED test:

```python
def test_repeated_primary_revision_mismatch_is_rejected_without_repair() -> None:
    draft = primary_specialist_primary_draft(return_revision="v2")
    result = validate_composition_candidate(draft, valid_context())
    assert result.status is CompositionValidationStatus.FAIL
    assert result.candidate.validity is CompositionValidity.REJECTED
    assert "repeated_primary_identity" in tuple(issue.issue_id for issue in result.issues)
    assert draft.nodes[-1].model_record.revision == "v2"
```

- [ ] **Step 2: Run RED verification**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_composition_validation.py -q
```

Expected failure: test collection raises `ModuleNotFoundError: No module named 'mercury.composition.validation'`.

- [ ] **Step 3: Implement independent fail-closed validation**

Add frozen result/issue/context contracts; exact input identity checks; ID recomputation; certified pattern comparison; repeated-identity checks; topological reachability; registry exact-record checks; per-stage compatibility reuse; complete requirement coverage; typed handoff checks; explicit evidence checks; provenance and nested boundary checks; stable issue sorting; and immutable final candidate construction. Do not change a draft, skip an invalid stage, relax requirements, rank results, or aggregate across candidates.

- [ ] **Step 4: Run focused GREEN verification**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_composition_validation.py -q
```

Expected result: all Task 4 focused tests pass.

- [ ] **Step 5: Run the full regression once**

Run only after focused GREEN:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

Expected result: the complete suite passes once from the final Task 4 state.

- [ ] **Step 6: Create the Task 4 checkpoint**

Stage only `src/mercury/composition/validation.py` and `tests/test_composition_validation.py`, verify the staged file list, and commit:

```powershell
git commit -m "feat: add Phase 5 composition validation baseline"
```

**STOP boundary:** Stop after Task 4 reporting. Do not begin Task 5.

---

## Task 5: Candidate Deduplication & Bounded Generation

**Files:**

- Create: `src/mercury/composition/generation.py`
- Create: `tests/test_composition_generation.py`
- Modify: none

**Interfaces consumed:**

- `CompositionGenerationPolicy`, `CompositionGenerationMetadata`, `CompositionResult`, `CompositionResultStatus`, candidate/draft/provenance contracts, constants, and canonical identity helper
- `CompositionInstantiationRequest` and `iter_composition_candidate_drafts`
- `CompositionValidationContext`, `CompositionValidationResult`, and `validate_composition_candidate`

**Frozen public interfaces produced:**

- `CompositionGenerationRequest(ContractModel)` with one instantiation request and a bounded generation policy
- `semantic_candidate_signature(draft: CompositionCandidateDraft) -> str`
- `merge_duplicate_drafts(left: CompositionCandidateDraft, right: CompositionCandidateDraft) -> CompositionCandidateDraft`
- `generate_compositions(request: CompositionGenerationRequest) -> CompositionResult`

The signature includes schema version, topology, ordered roles, exact model identities/revisions, edges, artifact contracts, and assigned hard requirements, but excludes provenance/evidence ordering. Duplicate merge requires equal signatures and performs sorted set union of provenance, evidence assessments, and justifications without changing semantic fields or composition ID.

`generate_compositions` consumes the Task 3 iterator lazily in canonical order, merges duplicates online, validates unique drafts independently, and stops after observing the first unique draft beyond `max_candidates`. Both valid and rejected candidates count toward the emission cap. It emits at most the cap, preserves valid and rejected candidates separately, and records `enumeration_complete=False`, `truncated=True`, a nonblank deterministic reason, and `candidate_count_lower_bound=max_candidates + 1` when capped. It never computes or claims an exact total after early stop.

Overall status is `READY` when any valid candidate remains, `FAIL` when composition is required and no valid candidate remains, and `NOT_APPLICABLE` only when the input explicitly marks composition unnecessary and no candidate is emitted. Rejected candidates do not invalidate valid candidates. Canonical order never implies preference.

- [ ] **Step 1: Write focused generation tests**

Test semantic duplicate collapse; distinct candidate preservation; provenance/evidence union; deterministic signatures and order; 3-node enforcement; caller limits of 1 through 256; rejection above certified maxima; lazy stop at `cap + 1`; transparent truncation metadata; total emitted valid+rejected count not exceeding cap; independent rejected retention; zero/one/many valid outputs; `READY`, `FAIL`, and `NOT_APPLICABLE`; identical input equality; input/result immutability; and absence of ranking/selection/fallback semantics.

Representative RED test:

```python
def test_candidate_cap_is_lazy_transparent_and_nonpreferential() -> None:
    result = generate_compositions(generation_request(max_candidates=2, available_bindings=3))
    assert len(result.valid_candidates) + len(result.rejected_candidates) == 2
    assert result.metadata.truncated is True
    assert result.metadata.enumeration_complete is False
    assert result.metadata.candidate_count_lower_bound == 3
    assert "canonical" in result.metadata.canonical_order_description
```

- [ ] **Step 2: Run RED verification**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_composition_generation.py -q
```

Expected failure: test collection raises `ModuleNotFoundError: No module named 'mercury.composition.generation'`.

- [ ] **Step 3: Implement semantic deduplication and bounded lazy generation**

Add the frozen request contract, canonical semantic hashing, strict duplicate merge, bounded online seen-signature tracking, independent Task 4 validation, separate valid/rejected accumulation, exact status rules, and complete truncation metadata. Keep memory proportional to emitted unique candidates and never sort by capability breadth, status, provider, quality, cost, latency, or any preference proxy.

- [ ] **Step 4: Run focused GREEN verification**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_composition_generation.py -q
```

Expected result: all Task 5 focused tests pass.

- [ ] **Step 5: Run the full regression once**

Run only after focused GREEN:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

Expected result: the complete suite passes once from the final Task 5 state.

- [ ] **Step 6: Create the Task 5 checkpoint**

Stage only `src/mercury/composition/generation.py` and `tests/test_composition_generation.py`, verify the staged file list, and commit:

```powershell
git commit -m "feat: add Phase 5 bounded composition generation baseline"
```

**STOP boundary:** Stop after Task 5 reporting. Do not begin Task 6.

---

## Task 6: Integration & Failure Hardening

**Files:**

- Create: `tests/test_composition_integration_failures.py`
- Modify by default: none
- Modify only when a focused adversarial test proves a real defect: the single owning file among `src/mercury/composition/contracts.py`, `src/mercury/composition/patterns.py`, `src/mercury/composition/instantiation.py`, `src/mercury/composition/validation.py`, or `src/mercury/composition/generation.py`

**Interfaces consumed:**

- Complete Phase 2 `WorkloadIntelligencePipelineResult`
- Complete Phase 3 `ExecutionGraph`, graph validation/readiness artifacts, and provenance
- Complete Phase 4 registry, compatibility, discovery, and evidence contracts
- Every public Phase 5 Task 1–5 type and function

**Public interfaces produced:** none. This task adds adversarial certification evidence and only a test-proven minimal production correction if required.

The integration suite constructs real immutable artifacts through the complete Phase 2–5 lifecycle. It must prove exact identity/revision/provenance continuity, certified topology restriction, independent candidate failure, zero-valid failure, input/result immutability, deterministic equality/order/IDs/reasons, and full boundary isolation.

- [ ] **Step 1: Write adversarial integration tests**

Cover valid `SINGLE` and all six multi-stage shapes; malformed Phase 2 status; non-ready/stale Phase 3 validation; request/workload/session/graph drift; registry identity conflict; model revision substitution; capability inference attempts using deceptive model names; unsupported graph capability mapping; malformed pattern injection; self-edge/cycle/orphan/recursion/swarm attempts; unsupported role transition; repeated-primary substitution; incompatible handoffs; missing/stale/conflicting/simulated explicitly required evidence; absent optional evidence; semantic duplicate provenance loss; cap bypass; nested ranking/selection/graph-assignment/hardware/placement/scheduler/runtime leakage; one rejected plus one valid candidate; all rejected; and no source mutation.

Representative hardening assertion:

```python
def test_invalid_candidate_cannot_poison_independent_valid_candidate() -> None:
    result = generate_compositions(mixed_valid_and_invalid_request())
    assert result.status is CompositionResultStatus.READY
    assert len(result.valid_candidates) == 1
    assert len(result.rejected_candidates) == 1
    assert result.rejected_candidates[0].rejection_reasons
```

- [ ] **Step 2: Run the adversarial RED gate**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_composition_integration_failures.py -q
```

Expected failure reason: any failure must identify one concrete Task 1–5 invariant that unsafe upstream state can bypass, such as nested boundary leakage not being rejected or duplicate merge dropping provenance. If all adversarial assertions pass on their first run, record that no production defect was proven and do not manufacture a production change merely to force RED.

- [ ] **Step 3: Correct only a proven defect**

For each failing adversarial assertion, trace the unsafe state to its owning Task 1–5 boundary, keep the failing test unchanged, patch only the owning production file, and rerun the single failing test before the focused file. Do not redesign interfaces, add new topology shapes, or modify certified Phase 0–4 code.

- [ ] **Step 4: Run focused GREEN verification**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_composition_integration_failures.py -q
```

Expected result: every integration and adversarial test passes, and any production modification has a direct failing-test proof.

- [ ] **Step 5: Run the full regression once**

Run only after focused GREEN:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

Expected result: the complete suite passes once from the final Task 6 state.

- [ ] **Step 6: Create the Task 6 checkpoint**

Stage `tests/test_composition_integration_failures.py` plus only directly proven Task 1–5 production corrections, verify the staged file list, and commit:

```powershell
git commit -m "test: harden Phase 5 composition lifecycle"
```

**STOP boundary:** Stop after Task 6 reporting, including every proven production correction. Do not begin Task 7.

---

## Task 7: Phase 5 Certification

**Files:**

- Create: `src/mercury/certification/phase5.py`
- Create: `configs/certification/phase5.json`
- Create: `tests/test_phase5_certification.py`
- Modify: none unless certification tests prove a real Phase 5 defect; any such defect remains owned by and fixed in its Task 1–5 module with the certification test retained

**Interfaces consumed:**

- `ContractModel` and Phase 0–4 certification conventions
- Task 1–6 test evidence and the complete Phase 5 public surface
- Machine-readable Phase 5 JSON configuration

**Frozen public interfaces produced:**

- `REQUIRED_PHASE5_GATE_IDS: tuple[str, ...]` containing exactly: `composition_contract`, `certified_pattern_library`, `candidate_instantiation`, `composition_validation`, `bounded_generation`, `integration_failure_hardening`, `identity_consistency`, `provenance_consistency`, `handoff_capability_evidence`, `determinism`, `fail_closed_behavior`, `boundary_compliance`, `full_regression_suite`, and `documentation`
- `KNOWN_PHASE5_CERTIFICATION_VIOLATIONS: frozenset[str]` covering malformed upstream state, identity/provenance drift, pattern drift, capability/handoff/evidence defects, nondeterminism, deduplication/provenance loss, bound bypass, and invalid independent-failure semantics
- `KNOWN_PHASE5_BOUNDARY_VIOLATIONS: frozenset[str]` covering ranking/scoring, winner selection, Phase 3 graph assignment, fallback/preference ordering, free-form topology generation, recursion/swarm behavior, hardware/placement, scheduling/runtime, cost/latency/quality optimization, and nested leakage
- `Phase5Gate(ContractModel)`
- `Phase5CertificationConfig(ContractModel)`
- `Phase5CertificationResult(ContractModel)`
- `evaluate_phase5_certification(config: Phase5CertificationConfig) -> Phase5CertificationResult`

The evaluator follows Phase 4 conventions: unique known gates, nonblank evidence, canonical required-gate order, known unique deterministic violation tuples, immutable result, pass/fail counts, missing-gate IDs, and `overall_passed=True` only when all 14 gates pass with no certification or boundary violations.

The checked-in JSON contains every gate exactly once, `passed: true`, repository-relative nonblank evidence, and empty violation collections. The `full_regression_suite` gate records the final Phase 5 full-suite command; `documentation` references the approved design and this implementation plan.

- [ ] **Step 1: Write focused certification tests**

Test complete 14-gate PASS; each missing gate; each failed gate; blank evidence; duplicate/unknown gates; malformed schema/config; every certification violation; every boundary violation including nested leakage; missing regression/documentation; immutable gate/result collections; deterministic canonical order; exact counts; and checked-in JSON PASS.

Representative RED test:

```python
def test_complete_phase5_certification_requires_all_14_gates() -> None:
    result = evaluate_phase5_certification(complete_config())
    assert result.overall_passed is True
    assert (result.passed_gate_count, result.failed_gate_count) == (14, 0)
    assert tuple(gate.gate_id for gate in result.gates) == REQUIRED_PHASE5_GATE_IDS
```

- [ ] **Step 2: Run RED verification**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_phase5_certification.py -q
```

Expected failure: test collection raises `ModuleNotFoundError: No module named 'mercury.certification.phase5'`; after the module exists but before the config is added, the checked-in-config test fails because `configs/certification/phase5.json` is absent.

- [ ] **Step 3: Implement certification contracts and configuration**

Add the required gate/violation constants, frozen gate/config/result contracts, validators, evaluator, and complete JSON configuration. Reject blank evidence, duplicates, unknown values, malformed schema versions, nondeterministic order, missing gates, failed gates, and any unresolved violation. Do not inspect runtime state, execute compositions, or broaden Phase 5 behavior.

- [ ] **Step 4: Run focused GREEN verification**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_phase5_certification.py -q
```

Expected result: all Task 7 focused certification tests pass.

- [ ] **Step 5: Run the full regression once**

Run only after focused GREEN:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

Expected result: every Phase 0–5 test passes once from the final Task 7 state.

- [ ] **Step 6: Evaluate the machine-readable certification**

Run:

```powershell
& .\.venv\Scripts\python.exe -c "import json; from pathlib import Path; from mercury.certification.phase5 import Phase5CertificationConfig, evaluate_phase5_certification; config = Phase5CertificationConfig.model_validate(json.loads(Path('configs/certification/phase5.json').read_text(encoding='utf-8'))); result = evaluate_phase5_certification(config); print(result.overall_passed, result.passed_gate_count, result.failed_gate_count, result.missing_gate_ids, result.certification_violations, result.boundary_violations)"
```

Expected result: `True 14 0 () () ()`.

- [ ] **Step 7: Create the Task 7 checkpoint**

Stage only `src/mercury/certification/phase5.py`, `configs/certification/phase5.json`, and `tests/test_phase5_certification.py` plus any separately proven Phase 5 correction, verify the staged file list, and commit:

```powershell
git commit -m "chore: certify MERCURY X Phase 5 baseline"
```

**STOP boundary:** Stop after reporting focused result, full-suite total, Phase 5 PASS/FAIL, 14-gate count, committed files, final Git status, and blockers. Do not begin Phase 6.
