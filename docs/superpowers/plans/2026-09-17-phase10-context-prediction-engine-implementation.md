MERCURY X — Phase 10 Context Prediction Engine Implementation Plan

For agentic workers: REQUIRED SUB-SKILL: Use superpowers (recommended) or superpowers to implement this plan task-by-task. Steps use checkbox (- [ ]) syntax for tracking.

Goal: Build a deterministic, explainable Context Prediction Engine that predicts which already-authorized context is likely to be needed next, with bounded confidence and one of three near-term horizons.

Architecture: Phase 10 consumes authorized Phase 8 session-memory records, authorized Phase 9 global-context records, and explicit task/dependency hints. It builds deterministic candidates, extracts transparent features, assigns one horizon and bounded confidence, assembles immutable predictions, and fails closed on authorization, lifecycle, closed-namespace, lineage, conflict, and limit violations. It does not retrieve, persist, prefetch, cache, place, schedule, or execute context.

Tech Stack: Python, Pydantic contract models, hashlib/json deterministic IDs, pytest, existing MERCURY X contracts/stores/retrieval modules.

Spec: docs/superpowers/specs/2026-09-17-phase10-context-prediction-engine-design.md

Global Constraints

Certified horizons are exactly NEXT_TURN, NEXT_TASK, SESSION_NEAR_TERM.

Certified confidence bands are exactly LOW, MEDIUM, HIGH.

MAX_PREDICTION_CANDIDATES = 256.

MAX_CONTEXT_PREDICTIONS = 64.

MAX_SOURCE_RECORDS_PER_PREDICTION = 128.

MAX_REASON_CODES = 16.

Equivalent inputs must produce identical candidate IDs, features, horizons, confidence, confidence bands, reason codes, prediction IDs, ordering, and fingerprints where applicable.

Exact namespace authorization is mandatory; no parent/child/sibling fallback.

Closed Phase 9 namespaces fail closed for Phase 10 baseline.

ACTIVE global records are eligible; SUPERSEDED is excluded by default; EXPIRED/REVOKED/TOMBSTONED are forbidden.

Conflicting Phase 9 context may be predicted but never resolved or winner-selected.

Phase 10 must not mutate Phase 8/9 inputs.

Phase 10 must not persist/promote memory, prefetch context, manage KV cache, select models, choose precision, place hardware, schedule runtime, migrate workloads, optimize cost/latency/quality, profile users, or predict personal behavior.

TDD is mandatory: RED → verify expected failure → minimal GREEN → focused tests → full regression exactly once → checkpoint.

Use repo root C:\Users\DELL\Downloads\Mercury-x.

Use .\.venv\Scripts\python.exe.

No worktree.

Use git -c safe.directory=C:/Users/DELL/Downloads/Mercury-x ....

On Windows, use unique external pytest temp/cache folders for full-suite runs when repo-local pytest temp/cache permissions fail.

File Structure

Phase 10 lives under a focused package:

src/mercury/context_prediction/contracts.py — enums, limits, candidate/feature/prediction contracts, deterministic identity helpers.

src/mercury/context_prediction/candidates.py — candidate construction from authorized Phase 8/9 sources.

src/mercury/context_prediction/features.py — deterministic explainable feature extraction.

src/mercury/context_prediction/scoring.py — horizon, confidence, confidence band, reason-code derivation.

src/mercury/context_prediction/predictor.py — immutable prediction assembly, caps, canonical ordering.

src/mercury/context_prediction/integration.py — bounded integration helpers and Phase 8/9 governance checks only where a dedicated coordinator is needed.

configs/certification/phase10.json — machine-readable certification checklist.

src/mercury/certification/phase10.py — fail-closed certification evaluator.

tests/test_context_prediction_contracts.py

tests/test_context_prediction_candidates.py

tests/test_context_prediction_features.py

tests/test_context_prediction_scoring.py

tests/test_context_prediction_predictor.py

tests/test_context_prediction_integration_failures.py

tests/test_phase10_certification.py

No existing Phase 0–9 production file should be modified unless a concrete incompatibility is proven by a failing test. If one is proven, stop and perform a bounded compatibility amendment at the source contract/store boundary before resuming.

Task 1: Context Prediction Contract Baseline

Files:

Create: src/mercury/context_prediction/contracts.py

Create: tests/test_context_prediction_contracts.py

Interfaces:

Consumes: GlobalMemoryNamespace, Phase 8/9 record IDs as opaque source identifiers.

Produces:

ContextPredictionHorizon

ContextConfidenceBand

ContextPredictionReasonCode

ContextPredictionCandidate

ContextPredictionFeatureVector

ContextPrediction

ContextPredictionRequest

ContextPredictionResult

deterministic identity helpers

exact Phase 10 limit constants

Step 1: Write failing contract tests

Cover exact enum membership, all limit constants, bounded confidence, positive creation sequence, nonblank predictor ID/version, canonical unique source IDs, canonical reason codes, deterministic candidate/prediction identity, invalid confidence rejection, duplicate source/reason rejection, and exact namespace identity validation.

Focused command:

.\.venv\Scripts\python.exe -m pytest tests/test_context_prediction_contracts.py -q

Expected RED: import failure because mercury.context_prediction.contracts does not yet exist.

Step 2: Implement the minimal contract module

Required constants:

MAX_PREDICTION_CANDIDATES = 256
MAX_CONTEXT_PREDICTIONS = 64
MAX_SOURCE_RECORDS_PER_PREDICTION = 128
MAX_REASON_CODES = 16

Required enums:

class ContextPredictionHorizon(str, Enum):
    NEXT_TURN = "NEXT_TURN"
    NEXT_TASK = "NEXT_TASK"
    SESSION_NEAR_TERM = "SESSION_NEAR_TERM"

class ContextConfidenceBand(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class ContextPredictionReasonCode(str, Enum):
    TASK_CONTINUITY = "TASK_CONTINUITY"
    CONTEXT_RECURRENCE = "CONTEXT_RECURRENCE"
    DEPENDENCY_ADJACENCY = "DEPENDENCY_ADJACENCY"
    SOURCE_LINEAGE_OVERLAP = "SOURCE_LINEAGE_OVERLAP"
    ARTIFACT_CONTINUITY = "ARTIFACT_CONTINUITY"
    SESSION_GLOBAL_AGREEMENT = "SESSION_GLOBAL_AGREEMENT"
    CONFLICT_PRESENT = "CONFLICT_PRESENT"
    NEAR_TERM_SESSION_SIGNAL = "NEAR_TERM_SESSION_SIGNAL"

Required contracts:

class ContextPredictionCandidate(ContractModel):
    namespace_type: GlobalMemoryNamespace
    namespace_id: str
    context_key: str
    candidate_id: str
    source_global_record_ids: tuple[str, ...] = ()
    source_phase8_record_ids: tuple[str, ...] = ()
    source_artifact_ids: tuple[str, ...] = ()
    conflict_present: bool = False
    creation_sequence: int

class ContextPredictionFeatureVector(ContractModel):
    candidate_id: str
    recency: float
    task_continuity: float
    context_key_recurrence: float
    dependency_adjacency: float
    source_lineage_overlap: float
    artifact_continuity: float
    session_global_agreement: float
    lifecycle_eligibility: float
    conflict_state: float
    horizon_compatibility: float

class ContextPrediction(ContractModel):
    prediction_id: str
    namespace_type: GlobalMemoryNamespace
    namespace_id: str
    context_key: str
    source_global_record_ids: tuple[str, ...]
    source_phase8_record_ids: tuple[str, ...]
    prediction_horizon: ContextPredictionHorizon
    confidence: float
    confidence_band: ContextConfidenceBand
    reason_codes: tuple[ContextPredictionReasonCode, ...]
    creation_sequence: int
    predictor_id: str
    predictor_version: str

class ContextPredictionRequest(ContractModel):
    namespace_type: GlobalMemoryNamespace
    namespace_id: str
    authorized_namespace_type: GlobalMemoryNamespace
    authorized_namespace_id: str
    predictor_id: str
    predictor_version: str
    limit: int = Field(default=64, ge=1, le=64)

class ContextPredictionResult(ContractModel):
    predictions: tuple[ContextPrediction, ...]

Identity helpers must use sha256 over canonical JSON with sort_keys=True and stable tuple/list ordering. No wall clock, random, machine, filesystem, Python hash, or process state.

Step 3: Focused GREEN

.\.venv\Scripts\python.exe -m pytest tests/test_context_prediction_contracts.py -q

Step 4: Full regression exactly once

$stamp = Get-Date -Format "yyyyMMddHHmmss"
$bt = Join-Path $env:TEMP "mercury-pytest-$stamp"
$cache = Join-Path $env:TEMP "mercury-cache-$stamp"
.\.venv\Scripts\python.exe -m pytest tests -q --basetemp="$bt" -o cache_dir="$cache"

Step 5: Commit

git -c safe.directory=C:/Users/DELL/Downloads/Mercury-x add src/mercury/context_prediction/contracts.py tests/test_context_prediction_contracts.py
git -c safe.directory=C:/Users/DELL/Downloads/Mercury-x commit -m "feat: add Phase 10 prediction contracts"
git -c safe.directory=C:/Users/DELL/Downloads/Mercury-x status

Task 2: Prediction Candidate Builder

Files:

Create: src/mercury/context_prediction/candidates.py

Create: tests/test_context_prediction_candidates.py

Interfaces:

Consumes:

ContextPredictionRequest

Phase 8 SessionMemoryRecord

Phase 9 GlobalContextRecord

Phase 9 GlobalContextStore

Produces:

def build_prediction_candidates(
    request: ContextPredictionRequest,
    *,
    session_records=(),
    global_store: GlobalContextStore | None = None,
    dependency_context_keys=(),
) -> tuple[ContextPredictionCandidate, ...]

Step 1: Write failing tests

Cover:

exact authorized namespace required

candidate creation from Phase 8 ACTIVE session records

candidate creation from Phase 9 ACTIVE global records

Phase 9 SUPERSEDED excluded by default

EXPIRED/REVOKED/TOMBSTONED rejected or excluded fail-closed

closed Phase 9 namespace rejected

cross-tenant/workspace/project rejected

no parent/child/sibling fallback

malformed provenance/source IDs rejected

same context key may merge authorized source lineage deterministically

conflict state preserved as conflict_present=True

candidate cap 256

equivalent input permutations produce identical candidate tuple and IDs

Phase 8/9 sources remain unchanged

Step 2: Verify RED

.\.venv\Scripts\python.exe -m pytest tests/test_context_prediction_candidates.py -q

Step 3: Implement candidate builder

Rules:

Validate ContextPredictionRequest.

Require (namespace_type, namespace_id) == (authorized_namespace_type, authorized_namespace_id).

If global_store is supplied, reject exact namespace when global_store.is_namespace_closed(...) is true.

Accept only exact-namespace eligible sources.

Group by exact context_key inside the authorized namespace.

Merge source IDs by sorted set, never merge across namespaces.

Preserve CONFLICTING as conflict_present=True.

Reject candidate source count above 128.

Reject total candidates above 256.

Order candidates canonically by:
namespace_type.value, namespace_id, context_key, candidate_id.

Step 4: Focused GREEN

.\.venv\Scripts\python.exe -m pytest tests/test_context_prediction_candidates.py -q

Step 5: Full regression exactly once and commit

Commit message:

feat: add Phase 10 prediction candidates

Task 3: Deterministic Feature Engine

Files:

Create: src/mercury/context_prediction/features.py

Create: tests/test_context_prediction_features.py

Interfaces:

Consumes ContextPredictionCandidate plus explicit current-task metadata.

Produces:

def extract_prediction_features(
    candidate: ContextPredictionCandidate,
    *,
    current_context_key: str | None = None,
    recent_context_keys=(),
    dependency_context_keys=(),
    current_artifact_ids=(),
    current_phase8_record_ids=(),
) -> ContextPredictionFeatureVector

Step 1: Write RED tests

Verify every feature is bounded [0.0, 1.0] and deterministic:

recency

task continuity

context-key recurrence

dependency adjacency

source-lineage overlap

artifact continuity

session/global agreement

lifecycle eligibility

conflict state

horizon compatibility

Also prove:

frequency alone never forces high score

conflict is represented, not resolved

equivalent permutation inputs produce same feature vector

source candidate is unchanged

malformed explicit task metadata fails closed

Step 2: Implement transparent deterministic formulas

Use simple explicit formulas only. Example baseline:

task_continuity = 1.0 if candidate.context_key == current_context_key else 0.0
context_key_recurrence = min(recent_context_keys.count(candidate.context_key) / 4.0, 1.0)
dependency_adjacency = 1.0 if candidate.context_key in dependency_context_keys else 0.0
source_lineage_overlap = overlap_ratio(candidate.source_phase8_record_ids, current_phase8_record_ids)
artifact_continuity = overlap_ratio(candidate.source_artifact_ids, current_artifact_ids)
session_global_agreement = 1.0 if candidate.source_phase8_record_ids and candidate.source_global_record_ids else 0.0
lifecycle_eligibility = 1.0
conflict_state = 0.0 if candidate.conflict_present else 1.0

recency and horizon_compatibility must derive only from explicit deterministic candidate/task metadata; if no certified recency metadata exists, use a neutral bounded baseline rather than wall-clock inference.

Step 3: Focused GREEN, full regression once, commit

Commit message:

feat: add Phase 10 deterministic features

Task 4: Horizon & Confidence Engine

Files:

Create: src/mercury/context_prediction/scoring.py

Create: tests/test_context_prediction_scoring.py

Interfaces:

Consumes ContextPredictionFeatureVector.

Produces:

def score_prediction(
    features: ContextPredictionFeatureVector,
) -> tuple[
    ContextPredictionHorizon,
    float,
    ContextConfidenceBand,
    tuple[ContextPredictionReasonCode, ...],
]

Step 1: Write RED tests

Prove:

output confidence always [0.0, 1.0]

NaN/inf are impossible/rejected

deterministic horizon

exact confidence-band boundaries

reason codes canonicalized and max 16

task continuity can drive NEXT_TURN

dependency adjacency can drive NEXT_TASK

weak but eligible signal can drive SESSION_NEAR_TERM

conflict emits CONFLICT_PRESENT

conflict does not select a winner

equivalent features produce identical outputs

Step 2: Implement explicit weighted scoring

Use a transparent weight table whose values sum to 1.0. Keep weights module constants and versioned through the predictor version supplied later.

Recommended baseline:

WEIGHTS = {
    "recency": 0.10,
    "task_continuity": 0.20,
    "context_key_recurrence": 0.10,
    "dependency_adjacency": 0.15,
    "source_lineage_overlap": 0.10,
    "artifact_continuity": 0.10,
    "session_global_agreement": 0.10,
    "lifecycle_eligibility": 0.05,
    "conflict_state": 0.05,
    "horizon_compatibility": 0.05,
}

Confidence bands:

LOW: confidence < 0.40
MEDIUM: 0.40 <= confidence < 0.75
HIGH: confidence >= 0.75

Horizon baseline:

NEXT_TURN: task_continuity >= 0.75
NEXT_TASK: dependency_adjacency >= 0.75 or source_lineage_overlap >= 0.75
SESSION_NEAR_TERM: otherwise

Reason codes are derived only from explicit feature thresholds.

Step 3: Focused GREEN, full regression once, commit

Commit message:

feat: add Phase 10 horizon confidence scoring

Task 5: Prediction Assembly & Ordering

Files:

Create: src/mercury/context_prediction/predictor.py

Create: tests/test_context_prediction_predictor.py

Interfaces:

Consumes candidates, feature vectors, score outputs, and ContextPredictionRequest.

Produces:

def assemble_context_predictions(
    request: ContextPredictionRequest,
    candidates,
    feature_vectors,
) -> ContextPredictionResult

The function may internally call score_prediction(...).

Step 1: Write RED tests

Cover:

deterministic prediction IDs

exact namespace preservation

source lineage preservation

max 128 source records per prediction

max 64 predictions

canonical reason-code tuple

predictor ID/version preserved

creation sequence deterministic

canonical ordering:

explicit horizon order

confidence descending

namespace type

namespace ID

context key

prediction ID

equivalent source/candidate permutation gives identical result

conflicting candidate remains conflict-traceable through reason code/source lineage

no Phase 8/9 mutation

Step 2: Implement immutable assembly

Use explicit horizon ordering:

HORIZON_ORDER = {
    ContextPredictionHorizon.NEXT_TURN: 0,
    ContextPredictionHorizon.NEXT_TASK: 1,
    ContextPredictionHorizon.SESSION_NEAR_TERM: 2,
}

Prediction ID canonical payload must include:

namespace

context key

sorted source IDs

horizon

confidence represented deterministically

confidence band

reason codes

creation sequence

predictor ID/version

Step 3: Focused GREEN, full regression once, commit

Commit message:

feat: assemble Phase 10 context predictions

Task 6: Integration, Governance & Adversarial Hardening

Files:

Create: src/mercury/context_prediction/integration.py only if coordination helpers are needed; do not create it for empty abstraction.

Create: tests/test_context_prediction_integration_failures.py

Interfaces:

Consumes all Phase 10 Task 1–5 interfaces and certified Phase 8/9 inputs.

Produces an end-to-end prediction path without new architectural behavior.

Step 1: Write adversarial integration tests

Exercise:

Phase 8 source
→ Phase 9 global context
→ candidate generation
→ features
→ horizon/confidence
→ prediction assembly
→ result

Required scenarios:

PROJECT exact namespace

WORKSPACE exact namespace

TENANT exact namespace

Phase 8-only candidate

Phase 9-only candidate

merged Phase 8 + Phase 9 candidate

conflicting Phase 9 source

NEXT_TURN result

NEXT_TASK result

SESSION_NEAR_TERM result

LOW/MEDIUM/HIGH bands

deterministic output under input permutations

Adversarial failures:

cross-tenant

cross-workspace

cross-project

parent/child fallback

sibling fallback

closed namespace

SUPERSEDED current prediction

EXPIRED

REVOKED

TOMBSTONED

malformed provenance

missing lineage



256 candidates



64 predictions



128 source records in one prediction



16 reason codes

invalid predictor ID/version

NaN/inf confidence

unsupported horizon/band

silent conflict winner

source mutation

semantic/vector ranker behavior

memory write/promotion behavior

prefetch/cache behavior

model/hardware/scheduler/runtime behavior

user-profile/personal-behavior prediction

Step 2: Implement only proven integration gaps

If tests expose a missing Phase 10 boundary, fix the smallest Phase 10 module.

If tests prove a Phase 8/9 contract/store omission, STOP and report the exact omission before changing certified prior-phase code.

Step 3: Focused GREEN

.\.venv\Scripts\python.exe -m pytest tests/test_context_prediction_integration_failures.py -q

Step 4: Full regression exactly once

Use unique Windows-safe temp/cache directories.

Step 5: Commit

test: harden Phase 10 context prediction boundaries

Task 7: Phase 10 Certification

Files:

Create: configs/certification/phase10.json

Create: src/mercury/certification/phase10.py

Create: tests/test_phase10_certification.py

Interfaces:

Mirrors the proven Phase 8/9 fail-closed certification style.

Required gate IDs:

horizons
confidence_bands
limits
candidate_identity
prediction_identity
namespace_authorization
namespace_isolation
closed_namespace
lifecycle_eligibility
source_traceability
source_immutability
deterministic_features
bounded_confidence
deterministic_confidence_band
deterministic_horizon
reason_codes
conflict_preservation
prediction_ordering
prediction_limit
source_limit
no_semantic_ranking
no_memory_persistence
no_prefetch_cache
no_execution_control
no_user_profile_prediction
adversarial_integration

Step 1: Write fail-closed certification tests

Verify:

complete config passes

missing gate fails

failed gate fails

unknown gate rejected

duplicate gate rejected

blank evidence rejected

non-config input rejected

Step 2: Implement phase10.py evaluator

Follow the Phase 9 pattern:

REQUIRED_PHASE10_GATE_IDS = (...)
class Phase10Gate(...)
class Phase10CertificationConfig(...)
class Phase10CertificationResult(...)
def evaluate_phase10_certification(...)
def main(...)

The evaluator must never hardcode PASS independent of gate data.

Step 3: Focused certification

.\.venv\Scripts\python.exe -m pytest tests/test_phase10_certification.py -q

Step 4: Certification evaluator

.\.venv\Scripts\python.exe -m mercury.certification.phase10

Expected: PASS.

Step 5: Final full regression

Use unique Windows-safe temp/cache directories.

Step 6: Final commit

git -c safe.directory=C:/Users/DELL/Downloads/Mercury-x add configs/certification/phase10.json src/mercury/certification/phase10.py tests/test_phase10_certification.py
git -c safe.directory=C:/Users/DELL/Downloads/Mercury-x commit -m "certify: complete Phase 10 context prediction engine"
git -c safe.directory=C:/Users/DELL/Downloads/Mercury-x status

Phase 10 is closed only when:

certification evaluator returns PASS

final full regression is green

working tree is clean

Then MERCURY X proceeds to Phase 11 — Semantic KV Cache.