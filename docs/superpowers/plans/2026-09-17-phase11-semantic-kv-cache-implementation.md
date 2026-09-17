MERCURY X — Phase 11 Semantic KV Cache Implementation Plan

For agentic workers: REQUIRED SUB-SKILL: Use superpowers (recommended) or superpowers to implement this plan task-by-task. Steps use checkbox (- [ ]) syntax for tracking.

Goal: Build a deterministic, namespace-isolated Semantic KV Cache that safely reuses authorized semantic context and, only under strict compatibility, physical KV-state references.

Architecture: Phase 11 consumes Phase 10 predictions and authorized Phase 8/9 lineage, performs deterministic lookup and compatibility evaluation, and returns semantic/physical reuse decisions. Physical KV payloads remain backend-neutral references so the entire control plane is testable on CPU-only machines. Phase 11 never schedules, places, executes, or migrates workloads.

Tech Stack: Python, Pydantic contract models, hashlib/json deterministic identities, pytest, existing MERCURY X Phase 9/10 contracts and stores.

Spec: docs/superpowers/specs/2026-09-17-phase11-semantic-kv-cache-design.md

Global Constraints

Reuse modes are exactly EXACT, SEMANTIC_COMPATIBLE, NO_REUSE.

Cache entry states are exactly ACTIVE, STALE, INVALIDATED.

MAX_KV_CACHE_ENTRIES_PER_NAMESPACE = 4096.

MAX_CACHE_LOOKUP_RESULTS = 64.

MAX_SOURCE_RECORDS_PER_CACHE_ENTRY = 128.

MAX_CACHE_DEPENDENCIES = 64.

MAX_CACHE_METADATA_BYTES = 65536.

Semantic similarity alone must never authorize physical KV reuse.

Physical KV reuse requires exact certified compatibility across model, model version, tokenizer, attention layout, KV format, precision, context generation, namespace, and valid payload identity.

Exact namespace authorization is mandatory with no parent/child/sibling fallback.

Closed namespaces fail closed.

STALE and INVALIDATED entries are excluded from current reuse.

Phase 10 predictions are hints only and never override authorization, lifecycle, compatibility, invalidation, or lineage rules.

Phase 11 must remain CPU-first and backend-neutral.

No model selection, precision selection/conversion, hardware placement, topology selection, scheduling, execution, migration, cost optimization, user profiling, or personal-behavior prediction.

TDD: RED → verify failure → minimal GREEN → focused tests → full regression once → checkpoint.

Repo root: C:\Users\DELL\Downloads\Mercury-x

Python: .\.venv\Scripts\python.exe

Git: git -c safe.directory=C:/Users/DELL/Downloads/Mercury-x ...

No worktree for this user-approved workflow.

Full pytest runs use unique Windows-safe temp/cache directories.

File Structure

src/mercury/semantic_kv_cache/contracts.py — enums, limits, payload/cache/lookup/reuse contracts and deterministic IDs.

src/mercury/semantic_kv_cache/identity.py — semantic keys, metadata fingerprints, canonical serialization/metadata-size enforcement.

src/mercury/semantic_kv_cache/compatibility.py — exact/semantic/physical KV reuse guard.

src/mercury/semantic_kv_cache/store.py — immutable namespace-isolated store and deterministic fingerprint.

src/mercury/semantic_kv_cache/lookup.py — structured bounded lookup and Phase 10 prediction hint integration.

src/mercury/semantic_kv_cache/governance.py — stale/invalidation/dependency-aware governance.

tests/test_semantic_kv_cache_contracts.py

tests/test_semantic_kv_cache_identity.py

tests/test_semantic_kv_cache_compatibility.py

tests/test_semantic_kv_cache_store.py

tests/test_semantic_kv_cache_lookup.py

tests/test_semantic_kv_cache_governance.py

tests/test_semantic_kv_cache_integration_failures.py

configs/certification/phase11.json

src/mercury/certification/phase11.py

tests/test_phase11_certification.py

Do not modify certified Phase 0–10 code unless a concrete incompatibility is proven by a failing test. If one is proven, stop and make the smallest bounded compatibility amendment with its own regression test and commit.

Task 1 — Semantic KV Cache Contract Baseline

Files:

Create: src/mercury/semantic_kv_cache/contracts.py

Create: tests/test_semantic_kv_cache_contracts.py

Produces:

SemanticKVReuseMode

SemanticKVCacheState

SemanticKVPayloadReference

SemanticKVCacheEntry

SemanticKVLookupRequest

SemanticKVLookupResult

SemanticKVCompatibilityResult

deterministic entry-ID helpers

exact Phase 11 limit constants

Write failing tests covering exact enum membership, exact limits, nonblank identities, canonical source/dependency tuples, state validation, payload-reference completeness, positive payload size, lookup limit, exact namespace authorization, and deterministic IDs.

Run focused RED:

.\.venv\Scripts\python.exe -m pytest tests/test_semantic_kv_cache_contracts.py -q

Implement minimal contracts and deterministic SHA-256 IDs using canonical JSON.

Run focused GREEN.

Run full regression once.

Commit:

feat: add Phase 11 semantic KV cache contracts

Task 2 — Deterministic Semantic Cache Identity

Files:

Create: src/mercury/semantic_kv_cache/identity.py

Create: tests/test_semantic_kv_cache_identity.py

Produces:

def make_semantic_cache_key(...)
def canonical_cache_metadata_payload(...)
def make_cache_metadata_fingerprint(...)
def validate_cache_metadata_size(...)

RED tests:

equivalent permutations → same semantic key

equivalent metadata → same fingerprint

namespace participates in identity

model/tokenizer/context generation participate where applicable

no wall-clock/random/process/machine dependence

metadata serialization deterministic

65536-byte metadata cap

oversized metadata fails closed

Implement canonical serialization with sorted keys and stable tuple ordering.

Focused GREEN.

Full regression once.

Commit:

feat: add deterministic Phase 11 cache identity

Task 3 — Compatibility & Reuse Guard

Files:

Create: src/mercury/semantic_kv_cache/compatibility.py

Create: tests/test_semantic_kv_cache_compatibility.py

Produces:

def evaluate_semantic_kv_compatibility(
    request: SemanticKVLookupRequest,
    entry: SemanticKVCacheEntry,
) -> SemanticKVCompatibilityResult

Rules:

exact namespace required

ACTIVE only

semantic reuse and physical KV reuse evaluated separately

semantic identity may yield SEMANTIC_COMPATIBLE

physical KV reuse requires exact:

model_id

model_version

tokenizer_id

attention_layout

kv_format

precision

context_generation

valid payload reference/fingerprint

semantic-only compatibility must never imply physical KV reuse

stale/invalidated → NO_REUSE

RED tests for every compatibility field independently.

Implement explicit fail-closed matrix.

Focused GREEN.

Full regression once.

Commit:

feat: add Phase 11 KV compatibility guard

Task 4 — Cache Store & Namespace Isolation

Files:

Create: src/mercury/semantic_kv_cache/store.py

Create: tests/test_semantic_kv_cache_store.py

Produces:

immutable SemanticKVCacheStore

register_cache_entry(...)

exact namespace lookup helpers

deterministic fingerprint

per-namespace capacity enforcement

duplicate/conflicting identity rejection

closed-namespace rejection using certified Phase 9 closure state when supplied

RED tests:

exact TENANT/WORKSPACE/PROJECT isolation

no fallback

namespace cap 4096

idempotent exact duplicate policy if selected by contract

conflicting duplicate rejected

deterministic fingerprint

closed namespace write rejected

source entry immutable after registration

Implement store.

Focused GREEN.

Full regression once.

Commit:

feat: add Phase 11 namespace isolated cache store

Task 5 — Lookup, Matching & Phase 10 Prediction Integration

Files:

Create: src/mercury/semantic_kv_cache/lookup.py

Create: tests/test_semantic_kv_cache_lookup.py

Produces:

def lookup_semantic_kv_cache(
    request: SemanticKVLookupRequest,
    store: SemanticKVCacheStore,
    *,
    prediction_ids=(),
) -> SemanticKVLookupResult

Rules:

structured exact namespace lookup

prediction IDs are optional hints only

result limit <= 64

canonical ordering:
reuse_mode → semantic_key → model_id → model_version → context_generation → creation_sequence → cache_entry_id

no vector/embedding ranker in baseline

Phase 10 hint cannot override lifecycle, namespace, compatibility, or invalidation

RED tests:

exact match

semantic-compatible match

no-reuse excluded from reusable results

prediction hint changes deterministic priority only where safe

prediction hint cannot force incompatible physical reuse

result cap

permutation invariance

cross-namespace prediction IDs do not widen authorization

Implement lookup.

Focused GREEN.

Full regression once.

Commit:

feat: add Phase 11 cache lookup and prediction hints

Task 6 — Lifecycle, Invalidation & Dependency Governance

Files:

Create: src/mercury/semantic_kv_cache/governance.py

Create: tests/test_semantic_kv_cache_governance.py

Produces:

def mark_cache_entry_stale(...)
def invalidate_cache_entry(...)
def invalidate_cache_dependencies(...)

Rules:

immutable transitions

ACTIVE → STALE

ACTIVE/STALE → INVALIDATED where policy permits

INVALIDATED terminal

deterministic transition IDs/metadata

reason required

lineage preserved

dependency invalidation follows explicit dependency graph only

dependency count <= 64

no heuristic broad invalidation

no silent deletion

RED tests for legal/illegal transitions, determinism, lineage preservation, terminal invalidation, dependency propagation, namespace isolation, and source immutability.

Implement governance.

Focused GREEN.

Full regression once.

Commit:

feat: add Phase 11 cache lifecycle governance

Task 7 — Integration & Adversarial Hardening

Files:

Create: tests/test_semantic_kv_cache_integration_failures.py

Modify only Phase 11 files if gaps are proven.

End-to-end path:

Phase 10 prediction
→ Phase 11 structured lookup
→ compatibility guard
→ semantic/physical reuse result
→ stale/invalidation governance

Required adversarial coverage:

TENANT exact scope

WORKSPACE exact scope

PROJECT exact scope

cross-tenant/workspace/project leakage

parent/child/sibling fallback

exact semantic reuse

semantic-only reuse

exact physical KV reuse

model mismatch

model-version mismatch

tokenizer mismatch

precision mismatch

attention-layout mismatch

KV-format mismatch

context-generation mismatch

incomplete payload metadata

invalid payload fingerprint

stale exclusion

invalidated exclusion

closed namespace

source-lineage preservation

source-record cap

dependency cap

metadata-size cap

namespace-cap overflow

prediction hint cannot override safety

input immutability

deterministic permutation invariance

no model selection

no precision conversion

no hardware placement

no scheduling

no runtime execution

no migration

no user profiling/personal-behavior prediction

Write adversarial tests.

Fix only proven Phase 11 gaps.

Focused GREEN.

Full regression once.

Commit:

test: harden Phase 11 semantic KV cache boundaries

Task 8 — Phase 11 Certification

Files:

Create: configs/certification/phase11.json

Create: src/mercury/certification/phase11.py

Create: tests/test_phase11_certification.py

Required certification gate IDs:

reuse_modes
cache_states
limits
semantic_identity
cache_entry_identity
metadata_size
namespace_authorization
namespace_isolation
closed_namespace
source_lineage
exact_compatibility
semantic_compatibility
physical_kv_compatibility
model_identity
model_version
tokenizer_identity
precision
attention_layout
kv_format
context_generation
payload_reference
payload_fingerprint
store_capacity
lookup_limit
source_limit
dependency_limit
lookup_ordering
stale_exclusion
invalidated_exclusion
deterministic_invalidation
dependency_invalidation
prediction_hint_only
no_semantic_only_physical_reuse
no_model_selection
no_precision_conversion
no_hardware_placement
no_scheduler_runtime
no_user_profile_prediction
adversarial_integration

Certification tests:

complete config passes

missing gate fails

failed gate fails

duplicate gate rejected

unknown gate rejected

blank evidence rejected

malformed config rejected

Implement fail-closed evaluator following Phase 9/10 style.

Focused certification:

.\.venv\Scripts\python.exe -m pytest tests/test_phase11_certification.py -q

Run evaluator:

.\.venv\Scripts\python.exe -m mercury.certification.phase11

Expected: PASS.

Final full regression:

$stamp = Get-Date -Format "yyyyMMddHHmmss"
$bt = Join-Path $env:TEMP "mercury-pytest-$stamp"
$cache = Join-Path $env:TEMP "mercury-cache-$stamp"
.\.venv\Scripts\python.exe -m pytest tests -q --basetemp="$bt" -o cache_dir="$cache"

Final commit:

git -c safe.directory=C:/Users/DELL/Downloads/Mercury-x add configs/certification/phase11.json src/mercury/certification/phase11.py tests/test_phase11_certification.py
git -c safe.directory=C:/Users/DELL/Downloads/Mercury-x commit -m "certify: complete Phase 11 semantic KV cache"
git -c safe.directory=C:/Users/DELL/Downloads/Mercury-x status

Phase 11 is closed only when:

focused tests are green

evaluator returns PASS

full regression is green

working tree is clean

Phase 10 behavior remains compatible

Phase 12 can consume stable Phase 11 contracts without changing Phase 11 semantics