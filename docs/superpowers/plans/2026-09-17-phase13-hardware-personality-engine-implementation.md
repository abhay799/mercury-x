MERCURY X — Phase 13 Hardware Personality Engine Implementation Plan

For agentic workers: REQUIRED SUB-SKILL: Use superpowers (recommended) or superpowers to implement this plan task-by-task. Steps use checkbox (- [ ]) syntax for tracking.

Goal: Build a deterministic, evidence-backed hardware personality engine that normalizes hardware descriptors, captures declared/probed/measured/derived evidence, resolves capabilities and workload affinities, evaluates compatibility, and certifies profile lifecycle without performing placement or scheduling.

Architecture: Phase 13 ingests static hardware descriptors, read-only capability probes, provider metadata, and benchmark evidence. It normalizes those inputs into immutable hardware profiles, resolves precision/memory/runtime/interconnect capabilities with explicit conflict handling, derives evidence-backed workload affinities, and exposes deterministic compatibility results for later topology/placement phases. All baseline logic remains CPU-first and backend-neutral.

Tech Stack: Python, Pydantic contract models, hashlib/json deterministic identities, pytest, standard-library CPU probes, existing MERCURY X Phase 12 contracts.

Spec: docs/superpowers/specs/2026-09-17-phase13-hardware-personality-engine-design.md

Global Constraints

Hardware classes are exactly CPU, GPU, TPU, NPU, OTHER_ACCELERATOR.

Evidence classes are exactly DECLARED, PROBED, MEASURED, DERIVED.

Trust states are exactly UNVERIFIED, VERIFIED, STALE, INVALID.

Capability support states are exactly CAPABLE, INCAPABLE, UNKNOWN.

Precision identifiers are exactly FP32, TF32, FP16, BF16, FP8, INT8, INT4.

Affinity scale is exactly LOW, MEDIUM, HIGH, UNKNOWN.

Absence of evidence maps to UNKNOWN, never silently to INCAPABLE.

Declared and measured values remain distinct.

Conflicting evidence remains visible and unresolved conflict normally yields UNKNOWN.

Equivalent inputs must produce identical IDs, profile fingerprints, affinity outputs, and compatibility results.

No random UUIDs, Python hash(), wall-clock scoring, or probe-order dependence.

CPU-only baseline certification: no CUDA/Triton/vLLM/GPU/TPU/NPU/RDMA requirement.

Probes are read-only and must not provision infrastructure or incur provider billing actions.

Phase 13 may evaluate Phase 12 requirements but must not select a device.

No model selection, precision selection/conversion, provider/region selection, placement, topology optimization, scheduling, migration, cost negotiation, scaling, or user profiling.

TDD: RED → expected failure → minimal GREEN → focused tests → full regression once → checkpoint.

Repo root: C:\Users\DELL\Downloads\Mercury-x

Python: .\.venv\Scripts\python.exe

Git: git -c safe.directory=C:/Users/DELL/Downloads/Mercury-x ...

No worktree for this user-approved workflow.

Full pytest uses unique Windows-safe temp/cache directories.

File Structure

src/mercury/hardware_personality/__init__.py — package boundary.

src/mercury/hardware_personality/contracts.py — enums, descriptors, evidence, profile, affinity, compatibility, lifecycle contracts and deterministic IDs.

src/mercury/hardware_personality/normalization.py — canonical descriptor normalization and malformed-input rejection.

src/mercury/hardware_personality/probes.py — probe adapter boundary, CPU-safe standard-library probe, synthetic fixture-friendly probe result construction.

src/mercury/hardware_personality/capabilities.py — precision/memory/runtime/software/interconnect support resolution and conflict handling.

src/mercury/hardware_personality/affinity.py — deterministic workload affinity derivation with evidence-backed reason codes.

src/mercury/hardware_personality/compatibility.py — workload requirement compatibility evaluation, including Phase 12 requirement shapes without placement.

src/mercury/hardware_personality/lifecycle.py — profile assembly, trust transitions, staleness, generation and fingerprinting.

tests/_phase13_helpers.py — deterministic fixtures.

tests/test_hardware_personality_contracts.py

tests/test_hardware_personality_normalization.py

tests/test_hardware_personality_probes.py

tests/test_hardware_personality_capabilities.py

tests/test_hardware_personality_affinity.py

tests/test_hardware_personality_compatibility.py

tests/test_hardware_personality_lifecycle.py

tests/test_hardware_personality_integration_failures.py

configs/certification/phase13.json

src/mercury/certification/phase13.py

src/mercury/certification/phase13_checks.py

tests/test_phase13_certification.py

Do not modify certified Phase 0–12 code unless a real typed compatibility test proves a contract mismatch. If that happens, stop and make the smallest bounded compatibility amendment separately.

Task 1 — Hardware Personality Contract Baseline

Files:

Create: src/mercury/hardware_personality/__init__.py

Create: src/mercury/hardware_personality/contracts.py

Create: tests/test_hardware_personality_contracts.py

Interfaces produced:

HardwareClass

HardwareEvidenceClass

HardwareTrustState

CapabilitySupportState

HardwarePrecision

HardwareAffinityDimension

HardwareAffinityLevel

HardwareCompatibilityState

VirtualizationState

HardwareDescriptor

HardwareEvidenceRecord

CapabilityAssessment

HardwareWorkloadAffinity

HardwarePersonalityProfile

HardwareRequirement

HardwareCompatibilityResult

deterministic identity helpers

Write RED tests for exact enums, required fields, canonical tuples, nonblank IDs, unknown behavior, evidence class separation, deterministic IDs, and fingerprint inputs.

Run:

.\.venv\Scripts\python.exe -m pytest tests/test_hardware_personality_contracts.py -q

Expected: import failure because Phase 13 package does not yet exist.

Implement minimal contracts with canonical JSON + SHA-256 helpers.

Focused GREEN.

Full regression once.

Commit:

feat: add Phase 13 hardware personality contracts

Task 2 — Hardware Descriptor & Normalization Engine

Files:

Create: src/mercury/hardware_personality/normalization.py

Create: tests/test_hardware_personality_normalization.py

Interfaces:

def normalize_hardware_descriptor(raw) -> HardwareDescriptor
def make_hardware_identity(descriptor: HardwareDescriptor) -> str

Rules:

canonical vendor/architecture/device text

canonical optional provider/region/instance metadata

nonnegative/positive numeric fields

deterministic identity

malformed descriptors fail closed

provider metadata retained only as metadata

no ranking or placement

RED tests for equivalent-normalization invariance, malformed fields, whitespace/case handling where explicitly allowed, and deterministic identity.

Implement normalization.

Focused GREEN.

Full regression once.

Commit:

feat: normalize Phase 13 hardware descriptors

Task 3 — Capability Probe & Evidence Model

Files:

Create: src/mercury/hardware_personality/probes.py

Create: tests/test_hardware_personality_probes.py

Interfaces:

class HardwareProbeBackend(Protocol):
    def probe(self, descriptor: HardwareDescriptor) -> tuple[HardwareEvidenceRecord, ...]: ...

class LocalCPUProbeBackend:
    def probe(self, descriptor: HardwareDescriptor) -> tuple[HardwareEvidenceRecord, ...]: ...

Rules:

CPU-safe and read-only

no privileged mutation

no cloud provisioning

no network requirement

deterministic canonical evidence ordering

synthetic accelerator probe fixtures supported in tests

DECLARED/PROBED/MEASURED/DERIVED remain distinct

synthetic fixture values are never labeled as real production MEASURED evidence

RED tests for protocol substitution, real CPU-safe probe shape, stable ordering, malformed probe output, and evidence-class separation.

Implement local CPU probe using safe standard-library/system introspection only.

Focused GREEN.

Full regression once.

Commit:

feat: add Phase 13 hardware probe evidence

Task 4 — Precision / Memory / Runtime Capability Matrix

Files:

Create: src/mercury/hardware_personality/capabilities.py

Create: tests/test_hardware_personality_capabilities.py

Interfaces:

def resolve_capability(
    property_name: str,
    evidence: tuple[HardwareEvidenceRecord, ...],
) -> CapabilityAssessment

def build_capability_matrix(
    evidence: tuple[HardwareEvidenceRecord, ...],
) -> tuple[CapabilityAssessment, ...]

Required capabilities include:

precision support for all certified precision IDs

memory capacity/bandwidth evidence

tensor-core-like acceleration

peer-to-peer support

unified memory

remote execution

virtualization

partitioning

software/runtime support

interconnect support

Rules:

no evidence → UNKNOWN

explicit trustworthy negative evidence → INCAPABLE

explicit trustworthy positive evidence → CAPABLE

unresolved positive/negative conflict → UNKNOWN

preserve all evidence IDs and conflict reason

declared/measured values never overwrite one another

RED tests for positive, negative, missing, and conflicting evidence.

Implement deterministic resolution.

Focused GREEN.

Full regression once.

Commit:

feat: add Phase 13 hardware capability matrix

Task 5 — Workload Affinity & Compatibility Engine

Files:

Create: src/mercury/hardware_personality/affinity.py

Create: src/mercury/hardware_personality/compatibility.py

Create: tests/test_hardware_personality_affinity.py

Create: tests/test_hardware_personality_compatibility.py

Interfaces:

def derive_workload_affinities(
    descriptor: HardwareDescriptor,
    capabilities: tuple[CapabilityAssessment, ...],
    evidence: tuple[HardwareEvidenceRecord, ...],
) -> tuple[HardwareWorkloadAffinity, ...]

def evaluate_hardware_compatibility(
    profile: HardwarePersonalityProfile,
    requirement: HardwareRequirement,
) -> HardwareCompatibilityResult

Affinity dimensions are exactly:

PREFILL_AFFINITY

DECODE_AFFINITY

EMBEDDING_AFFINITY

TRAINING_AFFINITY

FINE_TUNING_AFFINITY

RETRIEVAL_AFFINITY

TOOL_WORKLOAD_AFFINITY

MEMORY_INTENSITY_TOLERANCE

COMMUNICATION_INTENSITY_TOLERANCE

Rules:

evidence-backed reason codes

deterministic LOW/MEDIUM/HIGH/UNKNOWN

insufficient evidence → UNKNOWN

no cloud price/queue/scheduler input

compatibility states: COMPATIBLE / INCOMPATIBLE / UNKNOWN

explicit minimum memory/precision/runtime/class requirements only

compatibility does not rank devices or select hardware

Phase 12 declarative requirements may be adapted explicitly, not duck-typed

RED tests for deterministic affinity, unknown behavior, evidence reasons, minimum-memory checks, precision support, accelerator requirements, and explicit Phase 12 integration.

Implement minimal deterministic rules.

Focused GREEN.

Full regression once.

Commit:

feat: add Phase 13 affinity and compatibility engines

Task 6 — Profile Lifecycle, Trust & Deterministic Identity

Files:

Create: src/mercury/hardware_personality/lifecycle.py

Create: tests/test_hardware_personality_lifecycle.py

Interfaces:

def build_hardware_personality_profile(...)
def transition_hardware_trust(...)
def refresh_hardware_profile(...)
def evaluate_profile_staleness(...)

Allowed trust transitions:

UNVERIFIED -> VERIFIED
VERIFIED -> STALE
UNVERIFIED -> INVALID
VERIFIED -> INVALID
STALE -> VERIFIED
STALE -> INVALID

INVALID is terminal for that generation.

Rules:

explicit generation/sequence reference

no datetime.now() trust/staleness logic

refresh creates a new generation

previous generation remains immutable/auditable

fingerprint covers descriptor, capabilities, evidence IDs, affinities, generation, trust state

equivalent profile inputs → identical fingerprint

RED tests for all legal/illegal transitions, deterministic staleness, new generation behavior, terminal INVALID state, and fingerprint invariance.

Implement lifecycle.

Focused GREEN.

Full regression once.

Commit:

feat: add Phase 13 hardware profile lifecycle

Task 7 — Integration & Adversarial Hardening

Files:

Create: tests/_phase13_helpers.py

Create: tests/test_hardware_personality_integration_failures.py

Modify only Phase 13 files for proven gaps.

Required scenarios:

real CPU descriptor/probe path

synthetic GPU fixture

synthetic TPU fixture

synthetic NPU fixture

OTHER_ACCELERATOR fixture

missing evidence → UNKNOWN

positive/negative conflict → UNKNOWN

declared vs measured bandwidth remain distinct

malformed evidence rejection

duplicate evidence handling

evidence permutation invariance

profile fingerprint permutation invariance

stale evidence behavior

invalid evidence behavior

unsupported precision

virtualization restrictions

software/runtime mismatch

interconnect unknown behavior

exact Phase 12 requirement adaptation

no provider ranking

no region ranking

no hardware placement

no precision selection

no global scheduling

no migration

no autonomous scaling

no user profiling

input immutability

Write adversarial tests.

Fix only proven Phase 13 gaps.

Focused GREEN:

.\.venv\Scripts\python.exe -m pytest tests/test_hardware_personality_integration_failures.py -q

Run Phase 12 compatibility tests.

Full regression once.

Commit:

test: harden Phase 13 hardware personality boundaries

Task 8 — Phase 13 Certification

Files:

Create: configs/certification/phase13.json

Create: src/mercury/certification/phase13.py

Create: src/mercury/certification/phase13_checks.py

Create: tests/test_phase13_certification.py

Required gate IDs:

hardware_classes
evidence_classes
trust_states
capability_states
precision_identifiers
affinity_dimensions
affinity_scale
hardware_identity
evidence_identity
profile_identity
profile_fingerprint
descriptor_normalization
declared_measured_separation
evidence_lineage
evidence_conflict_preservation
unknown_insufficient_evidence
precision_resolution
memory_capability
runtime_capability
software_stack
interconnect_capability
virtualization
cpu_probe_path
synthetic_accelerators
affinity_determinism
affinity_evidence
compatibility_determinism
compatibility_unknown
phase12_requirement_integration
profile_generation
trust_transitions
deterministic_staleness
invalid_terminality
no_model_selection
no_precision_selection
no_provider_selection
no_region_selection
no_hardware_placement
no_global_scheduling
no_migration
no_autonomous_scaling
adversarial_integration

Certification requirements:

exact required gate set

missing gate fails

duplicate gate fails

unknown gate fails

malformed check metadata fails

executable checks in phase13_checks.py

a manually edited passed: true is not sufficient

CPU-only and fast

no fake benchmark evidence

Write fail-closed certification tests.

Implement executable gate registry/checks.

Focused certification:

.\.venv\Scripts\python.exe -m pytest tests/test_phase13_certification.py -q

Evaluator:

.\.venv\Scripts\python.exe -m mercury.certification.phase13

Expected: PASS.

Phase 12 compatibility:

.\.venv\Scripts\python.exe -m pytest `
tests/test_disaggregated_execution_contracts.py `
tests/test_disaggregated_execution_graph.py `
tests/test_disaggregated_execution_handoffs.py `
tests/test_disaggregated_execution_readiness.py `
tests/test_disaggregated_execution_integration.py `
tests/test_disaggregated_execution_results.py `
tests/test_disaggregated_execution_integration_failures.py `
tests/test_phase12_certification.py -q

Final full regression:

$stamp = Get-Date -Format "yyyyMMddHHmmss"
$bt = Join-Path $env:TEMP "mercury-pytest-$stamp"
$cache = Join-Path $env:TEMP "mercury-cache-$stamp"
.\.venv\Scripts\python.exe -m pytest tests -q --basetemp="$bt" -o cache_dir="$cache"

Verify diff:

git -c safe.directory=C:/Users/DELL/Downloads/Mercury-x diff --check
git -c safe.directory=C:/Users/DELL/Downloads/Mercury-x status --short --untracked-files=all

Final implementation commit after review:

certify: complete Phase 13 hardware personality engine

Phase 13 is closed only when:

focused Phase 13 tests pass

Phase 13 executable certification returns PASS

Phase 12 compatibility passes

full repository regression passes

diff check passes

working tree is clean after commit

no placement/scheduling/migration/provider-selection responsibility leaks into Phase 13