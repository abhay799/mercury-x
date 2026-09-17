MERCURY X — Phase 12 Disaggregated Cognitive Execution Implementation Plan

For agentic workers: REQUIRED SUB-SKILL: Use superpowers (recommended) or superpowers to implement this plan task-by-task. Steps use checkbox (- [ ]) syntax for tracking.

Goal: Build a deterministic, namespace-isolated disaggregated execution control plane that decomposes AI workloads into certified execution segments with explicit handoffs, readiness, retry, verification, and result-stitching rules.

Architecture: Phase 12 consumes existing execution-graph intent plus Phase 10 prediction hints and Phase 11 KV/context references. It constructs an immutable execution-segment DAG, enforces explicit handoff contracts, evaluates readiness, governs state transitions and retries, validates KV/context references, and stitches verified terminal results. It remains backend-neutral and does not select hardware, placement, provider, region, precision, or global schedule.

Tech Stack: Python, Pydantic contract models, hashlib/json deterministic identities, pytest, existing MERCURY X Phase 9–11 contracts.

Spec: docs/superpowers/specs/2026-09-17-phase12-disaggregated-cognitive-execution-design.md

Global Constraints

Segment types are exactly PREFILL, DECODE, TOOL_EXECUTION, RETRIEVAL, TRANSFORM, AGGREGATION.

Execution states are exactly PLANNED, READY, RUNNING, SUCCEEDED, FAILED, CANCELLED.

Handoff kinds are exactly ARTIFACT, CONTEXT, KV_REFERENCE, CONTROL.

Handoff states are exactly PENDING, AVAILABLE, CONSUMED, INVALIDATED.

MAX_SEGMENTS_PER_EXECUTION_PLAN = 256.

MAX_DEPENDENCIES_PER_SEGMENT = 64.

MAX_HANDOFFS_PER_SEGMENT = 64.

MAX_EXECUTION_ARTIFACTS_PER_SEGMENT = 128.

MAX_RETRY_ATTEMPTS = 8.

Equivalent inputs must produce identical segment IDs, handoff IDs, plan IDs, fingerprints, ordering, and stitched-result IDs.

Exact namespace authorization is mandatory; no tenant/workspace/project parent-child-sibling fallback.

Closed namespaces fail closed.

Phase 11 STALE or INVALIDATED entries cannot back KV_REFERENCE handoffs.

Phase 10 predictions are hints only and may not force execution or bypass checks.

Phase 12 must not mutate Phase 3/9/10/11 objects.

Phase 12 must not perform model selection, precision selection/conversion, hardware/provider/region placement, global scheduling, migration, fleet optimization, or user profiling.

CPU-only control-plane execution is mandatory for baseline certification.

TDD: RED → verify expected failure → minimal GREEN → focused tests → full regression once → checkpoint.

Repo root: C:\Users\DELL\Downloads\Mercury-x

Python: .\.venv\Scripts\python.exe

Git: git -c safe.directory=C:/Users/DELL/Downloads/Mercury-x ...

No worktree for this user-approved workflow.

Full pytest uses unique Windows-safe temp/cache directories.

File Structure

src/mercury/disaggregated_execution/contracts.py — enums, limits, segment/handoff/plan/retry/failure/result contracts, deterministic ID helpers.

src/mercury/disaggregated_execution/graph.py — segment DAG assembly, cycle detection, entry/terminal detection, plan fingerprinting.

src/mercury/disaggregated_execution/handoffs.py — handoff creation and state transitions.

src/mercury/disaggregated_execution/readiness.py — readiness and execution-state transition rules.

src/mercury/disaggregated_execution/integration.py — Phase 10 prediction hints + Phase 11 KV/context reference validation.

src/mercury/disaggregated_execution/results.py — failure classification, retry policy, verification gates, deterministic result stitching.

tests/test_disaggregated_execution_contracts.py

tests/test_disaggregated_execution_graph.py

tests/test_disaggregated_execution_handoffs.py

tests/test_disaggregated_execution_readiness.py

tests/test_disaggregated_execution_integration.py

tests/test_disaggregated_execution_results.py

tests/test_disaggregated_execution_integration_failures.py

configs/certification/phase12.json

src/mercury/certification/phase12.py

tests/test_phase12_certification.py

Do not modify certified Phase 0–11 code unless a failing compatibility test proves a real contract mismatch. If that happens, stop and make the smallest bounded compatibility amendment in a separate commit before resuming.

Task 1 — Disaggregated Execution Contract Baseline

Files:

Create: src/mercury/disaggregated_execution/contracts.py

Create: tests/test_disaggregated_execution_contracts.py

Interfaces produced:

ExecutionSegmentType

ExecutionSegmentState

ExecutionHandoffKind

ExecutionHandoffState

ExecutionFailureCategory

ExecutionRetryPolicy

ExecutionSegment

ExecutionHandoff

DisaggregatedExecutionPlan

SegmentExecutionResult

StitchedExecutionResult

deterministic ID helpers

exact Phase 12 limit constants

Write RED tests for exact enums, exact limits, canonical tuples, nonblank identities, bounded retry count, deterministic IDs, namespace identity, source immutability, and result/fingerprint fields.

Run:

.\.venv\Scripts\python.exe -m pytest tests/test_disaggregated_execution_contracts.py -q

Expected: import failure because Phase 12 contracts do not yet exist.

Implement minimal contracts with canonical JSON + SHA-256 helpers.

Focused GREEN.

Full regression once.

Commit:

feat: add Phase 12 execution contracts

Task 2 — Execution Segment Graph Builder

Files:

Create: src/mercury/disaggregated_execution/graph.py

Create: tests/test_disaggregated_execution_graph.py

Interfaces:

def build_disaggregated_execution_plan(
    *,
    namespace_type,
    namespace_id,
    source_execution_graph_id,
    segments,
    handoffs=(),
    plan_version="1",
    creation_sequence=1,
) -> DisaggregatedExecutionPlan

Rules:

max 256 segments

no duplicate IDs

no self-dependency

no dangling dependency

no duplicate dependency edge

DAG required

deterministic topological/canonical ordering

deterministic entry/terminal IDs

deterministic plan fingerprint

exact namespace consistency

RED tests for every graph invariant.

Implement cycle detection and deterministic plan assembly.

Focused GREEN.

Full regression once.

Commit:

feat: add Phase 12 execution graph builder

Task 3 — Handoff Contract & State Engine

Files:

Create: src/mercury/disaggregated_execution/handoffs.py

Create: tests/test_disaggregated_execution_handoffs.py

Interfaces:

def create_execution_handoff(...)
def make_handoff_available(...)
def consume_handoff(...)
def invalidate_handoff(...)

Rules:

producer and consumer must exist

exact namespace required

producer != consumer

state matrix:

PENDING -> AVAILABLE

AVAILABLE -> CONSUMED

PENDING -> INVALIDATED

AVAILABLE -> INVALIDATED

CONSUMED and INVALIDATED terminal

only declared consumer may consume

invalidation reason required

immutable transitions

deterministic IDs

RED tests for legal/illegal transitions, consumer authorization, namespace isolation, lineage, and determinism.

Implement minimal engine.

Focused GREEN.

Full regression once.

Commit:

feat: add Phase 12 handoff state engine

Task 4 — Segment Readiness & Dependency Engine

Files:

Create: src/mercury/disaggregated_execution/readiness.py

Create: tests/test_disaggregated_execution_readiness.py

Interfaces:

def evaluate_segment_readiness(segment, *, segments, handoffs) -> bool
def transition_segment_state(segment, target_state, *, retry_policy=None, attempt=1)

Rules:

PLANNED → READY only when all dependencies SUCCEEDED and all required handoffs AVAILABLE

READY → RUNNING

RUNNING → SUCCEEDED only through verified completion path

RUNNING → FAILED

PLANNED/READY/RUNNING → CANCELLED

FAILED → READY only when retry policy permits and attempt <= 8

SUCCEEDED/CANCELLED terminal

no hidden state changes

RED tests for readiness, dependencies, handoffs, cancellation, retry gating, and forbidden transitions.

Implement deterministic transition matrix.

Focused GREEN.

Full regression once.

Commit:

feat: add Phase 12 readiness and state transitions

Task 5 — Phase 11 KV / Context Integration

Files:

Create: src/mercury/disaggregated_execution/integration.py

Create: tests/test_disaggregated_execution_integration.py

Interfaces:

def validate_kv_handoff_reference(handoff, cache_entry, compatibility_result) -> None
def validate_context_handoff_reference(handoff, *, authorized_namespace_type, authorized_namespace_id) -> None
def apply_prediction_hints(plan, prediction_ids=()) -> DisaggregatedExecutionPlan

Rules:

KV_REFERENCE accepts only Phase 11 ACTIVE entries

Phase 11 physical compatibility cannot be overridden

stale/invalidated KV rejected

payload fingerprint preserved

exact namespace required

Phase 10 prediction hint may influence metadata/order only where explicit, never readiness or authorization

no cache mutation

no prediction mutation

RED tests for ACTIVE exact KV, stale/invalidated rejection, semantic-only no-physical override, context namespace isolation, and prediction hint-only behavior.

Implement bounded integration.

Focused GREEN.

Full regression once.

Commit:

feat: integrate Phase 12 with context and KV references

Task 6 — Failure, Retry & Result Stitching

Files:

Create: src/mercury/disaggregated_execution/results.py

Create: tests/test_disaggregated_execution_results.py

Interfaces:

def classify_execution_failure(...)
def can_retry_segment(...)
def verify_segment_result(...)
def stitch_execution_results(...)

Rules:

exact failure categories

retry attempts <= 8

retry only for declared categories

SUCCEEDED requires verification

terminal results must exist for every terminal segment

stitched result deterministic

preserve terminal result IDs + artifact lineage

missing required output fails closed

RED tests for all failure classes, retry eligibility, retry cap, verification-before-success, deterministic stitching, missing terminal output, and lineage preservation.

Implement minimal deterministic behavior.

Focused GREEN.

Full regression once.

Commit:

feat: add Phase 12 retry verification and result stitching

Task 7 — Integration & Adversarial Hardening

Files:

Create: tests/test_disaggregated_execution_integration_failures.py

Modify only Phase 12 files if a failing test proves a gap.

Required end-to-end scenarios:

PREFILL → KV_REFERENCE → DECODE

RETRIEVAL → CONTEXT → PREFILL

TOOL_EXECUTION → ARTIFACT → AGGREGATION

TRANSFORM → ARTIFACT → AGGREGATION

exact TENANT scope

exact WORKSPACE scope

exact PROJECT scope

cross-tenant/workspace/project failure

parent/child/sibling leakage rejection

cycle rejection

dangling dependency rejection

self-dependency rejection

duplicate segment rejection

handoff wrong-consumer rejection

handoff terminal-state behavior

closed namespace rejection

stale/invalidated Phase 11 KV rejection

Phase 10 hint cannot force execution

cancellation terminal behavior

retry limit and retry-category enforcement

verification failure

missing terminal result

deterministic permutation invariance

source immutability

no model selection

no precision selection/conversion

no provider/region/hardware placement

no global scheduling

no migration

no user-profile/personal-behavior prediction

Write adversarial tests.

Fix only proven Phase 12 gaps.

Focused GREEN:

.\.venv\Scripts\python.exe -m pytest tests/test_disaggregated_execution_integration_failures.py -q

Full regression once.

Commit:

test: harden Phase 12 execution boundaries

Task 8 — Phase 12 Certification

Files:

Create: configs/certification/phase12.json

Create: src/mercury/certification/phase12.py

Create: tests/test_phase12_certification.py

Required gate IDs:

segment_types
execution_states
handoff_kinds
handoff_states
limits
segment_identity
handoff_identity
plan_identity
plan_fingerprint
acyclic_graph
self_dependency
dangling_dependency
duplicate_segment
entry_terminal_detection
namespace_authorization
namespace_isolation
closed_namespace
handoff_endpoints
handoff_transitions
readiness_dependencies
readiness_handoffs
execution_transitions
cancellation_terminal
retry_limit
retry_eligibility
failure_classification
kv_compatibility
stale_invalidated_kv
prediction_hint_only
source_immutability
verification_before_success
result_stitching
missing_terminal_result
result_lineage
no_model_selection
no_precision_selection
no_hardware_placement
no_global_scheduling
no_migration
no_user_profile_prediction
adversarial_integration

Write fail-closed certification tests:

complete config passes

missing gate fails

failed gate fails

duplicate gate rejected

unknown gate rejected

blank evidence rejected

malformed config rejected

Implement Phase 12 evaluator following Phase 9–11 pattern.

Focused certification:

.\.venv\Scripts\python.exe -m pytest tests/test_phase12_certification.py -q

Evaluator:

.\.venv\Scripts\python.exe -m mercury.certification.phase12

Expected: PASS.

Final full regression:

$stamp = Get-Date -Format "yyyyMMddHHmmss"
$bt = Join-Path $env:TEMP "mercury-pytest-$stamp"
$cache = Join-Path $env:TEMP "mercury-cache-$stamp"
.\.venv\Scripts\python.exe -m pytest tests -q --basetemp="$bt" -o cache_dir="$cache"

Final commit:

git -c safe.directory=C:/Users/DELL/Downloads/Mercury-x add configs/certification/phase12.json src/mercury/certification/phase12.py tests/test_phase12_certification.py
git -c safe.directory=C:/Users/DELL/Downloads/Mercury-x commit -m "certify: complete Phase 12 disaggregated cognitive execution"
git -c safe.directory=C:/Users/DELL/Downloads/Mercury-x status

Phase 12 is closed only when:

focused Phase 12 tests pass

certification evaluator returns PASS

final full regression is green

working tree is clean

Phase 10/11 behavior remains compatible

no placement/scheduler/runtime responsibilities leak into Phase 12

After Phase 12 closes, run the previously planned Phase 10 hardening pass before continuing significantly further into MERCURY X.