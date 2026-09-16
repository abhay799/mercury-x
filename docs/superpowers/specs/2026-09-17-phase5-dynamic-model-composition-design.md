# MERCURY X Phase 5 Dynamic Model Composition Design

## Status and Scope

This document locks the design for Phase 5, Dynamic Model Composition. Phase 5
converts certified workload and logical execution-graph requirements, together
with Phase 4 model capability records and evidence assessments, into zero, one,
or many valid logical model-composition candidates.

Phase 5 describes possible logical compositions. It does not choose which
candidate will execute, bind a model to a Phase 3 graph node, or make any
physical execution decision.

## Purpose

Phase 5 answers:

> Which bounded, certified logical model compositions can satisfy this
> workload and execution graph with explicit capability and evidence support?

The output is a deterministic candidate set containing valid candidates and
independently rejected candidates with machine-readable reasons. A single
model is represented by the certified `SINGLE` topology; multi-model
compositions use only the certified topologies in this document.

## Phase Boundary

Phase 5 may:

- generate logical single-model and multi-model candidates;
- instantiate certified composition patterns;
- validate composition structure, capabilities, handoffs, identity, and
  evidence;
- preserve workload, graph, model, capability, and evidence provenance;
- reject invalid candidates with deterministic reasons; and
- deduplicate and bound candidate generation.

Phase 5 must not:

- rank candidates or expose rank-like ordering;
- score preferences, suitability, quality, cost, or latency;
- select a winner, primary candidate, fallback, or runner-up;
- assign models to Phase 3 execution-graph nodes;
- choose or match CPU, GPU, accelerator, device, host, or other hardware;
- perform physical placement, regional choice, or scheduling;
- optimize cost, latency, or quality;
- invoke a model, tool, retrieval system, scheduler, or runtime; or
- create open-ended swarms, recursive orchestration, self-calling loops, or
  dynamically invented topologies.

Candidate collection order is canonical serialization order only. It must
never be documented or consumed as preference, suitability, execution, or
fallback order.

## Inputs

Phase 5 consumes immutable, already-normalized artifacts:

1. Phase 2 workload intelligence identity and hard logical requirements.
2. A Phase 3 logical `ExecutionGraph` and passing readiness/validation
   evidence.
3. A Phase 4 `ModelCapabilityRegistry` snapshot.
4. Phase 4 hard `ModelCapabilityRequirements`, compatibility results, and
   candidate-discovery output where applicable.
5. Phase 4 capability evidence assessments for claims that carry explicit
   evidence requirements.
6. A frozen generation policy containing the certified node and candidate
   limits.

`request_id`, `workload_id`, `session_id`, and graph identity must agree across
all supplied artifacts. A registry record is addressed only by its exact
`provider`, `model_id`, `family`, and `revision`. Phase 5 must not infer a model
identity or capability from names, aliases, or free-form text.

Phase 5 must fail closed before candidate generation when an input contract is
malformed, the Phase 3 graph is not ready, identities disagree, the registry
snapshot is invalid, or required Phase 4 evidence is missing or malformed.

## Architecture

Phase 5 is divided into seven components that map directly to its seven tasks:

1. **Composition contracts** define immutable roles, patterns, nodes, edges,
   candidates, rejection reasons, generation metadata, and result status.
2. **Certified pattern library** contains the only topology definitions that
   may be instantiated in the certified baseline.
3. **Candidate instantiation engine** derives role requirements from certified
   workload and graph requirements, then binds exact Phase 4 records using
   deterministic rules.
4. **Composition validation engine** independently validates every candidate's
   structure, capability coverage, handoffs, evidence, identity, and
   provenance.
5. **Deduplication and bounded generation** canonicalizes candidates, merges
   duplicate provenance without loss, applies hard generation limits, and
   reports truncation explicitly.
6. **Integration and failure hardening** proves the lifecycle fails closed
   under malformed, conflicting, adversarial, and boundary-leaking input.
7. **Phase 5 certification** evaluates machine-readable gates for the complete
   composition baseline.

Dependencies flow in one direction. Pattern definitions do not depend on
candidate instances. Instantiation does not rewrite Phase 2–4 inputs.
Validation reports issues but does not repair candidates. Deduplication does
not alter semantic structure. Certification observes artifacts and evidence
without changing them.

## Component Responsibilities

### Composition contract layer

The contract layer defines frozen, strictly validated, versioned structures.
The baseline schema version is `mercury.model-composition/v1`.

A composition node contains:

- a deterministic stage identifier;
- one baseline role;
- the exact Phase 4 model identity and revision;
- the hard logical requirement assigned to the stage;
- explicit capability justification;
- evidence and provenance references; and
- declared logical input and output contracts used for handoff validation.

A composition edge contains deterministic source and target stage identifiers,
an allowed logical handoff type, the artifact or requirement carried across
the handoff, and nonblank justification. Edges describe logical information
flow only; they are not scheduler dependencies or runtime channels.

A composition candidate contains:

- schema version;
- deterministic `composition_id`;
- request, workload, session, and graph identity;
- certified pattern identifier;
- ordered nodes and edges;
- the requirements satisfied by the whole candidate;
- per-stage capability justification;
- workload, graph, registry, capability, and evidence provenance links;
- validity state; and
- deterministic rejection reasons.

Candidate validity has exactly two post-validation states: `VALID` and
`REJECTED`. A `VALID` candidate has no rejection reasons. A `REJECTED`
candidate has at least one nonblank, machine-readable rejection reason.
Unvalidated candidate drafts are internal to instantiation and cannot be
emitted as final Phase 5 candidates.

The result separates `valid_candidates` and `rejected_candidates`, retains the
frozen generation metadata, and exposes one of these statuses:

- `READY`: at least one valid candidate remains;
- `NOT_APPLICABLE`: the certified input declares that no model composition is
  required and no candidate is emitted; or
- `FAIL`: composition is required and no valid candidate remains.

### Certified pattern library

The library is data, not free-form orchestration code. Each pattern declares a
stable pattern identifier, ordered role slots, allowed edges, repeated-role
identity constraints, applicability requirements, and maximum node count.
Only the patterns listed in this specification are valid in the certified
baseline.

Pattern definitions are immutable and validated at construction. A definition
with an unknown role, unknown transition, cycle, self-edge, orphan slot,
duplicate stage identifier, more than three nodes, or an undeclared transition
is rejected before use.

### Candidate instantiation engine

The instantiation engine performs deterministic rule-based expansion of the
certified pattern library. It does not generate topology text, call an LLM, or
invent roles.

For each applicable pattern, it:

1. derives each role slot's hard requirements from the certified Phase 2 and
   Phase 3 artifacts;
2. obtains exact Phase 4 records satisfying those requirements through the
   compatibility and discovery contracts;
3. filters evidence only when the input explicitly requires hard evidence;
4. enumerates role bindings in canonical pattern, slot, and exact model
   identity order;
5. enforces repeated-role identity constraints; and
6. constructs immutable candidate drafts with complete provenance.

No raw user text, model-name keyword, fuzzy match, status preference, provider
preference, cost, latency, or quality value may influence instantiation.

### Composition validation engine

The validation engine evaluates each candidate independently. It returns a
deterministic validation result and ordered issues; it never rewrites a node,
edge, model binding, evidence record, or topology.

Validation covers:

- certified pattern conformance;
- DAG structure and complete entry-to-exit reachability;
- exact role and transition legality;
- exact model identity and revision consistency;
- per-stage Phase 4 hard capability compatibility;
- whole-candidate requirement coverage;
- logical input/output handoff compatibility;
- required evidence acceptability;
- provenance completeness; and
- phase-boundary compliance.

Every issue contains a stable issue identifier, affected stage or edge where
applicable, the violated invariant, and a nonblank reason. Issue ordering uses
stable identifiers and stage/edge identities.

### Deduplication and bounded generation

The bounded-generation component owns canonical identity, deduplication, and
resource-independent limits. It does not rank candidates.

The certified baseline hard limits are:

- `MAX_COMPOSITION_NODES = 3`; and
- `MAX_COMPOSITION_CANDIDATES = 256` emitted candidates per request.

A caller may request smaller positive limits but cannot exceed either certified
maximum. All seven certified topologies fit within the three-node limit.

The semantic deduplication key is derived from schema version, pattern
identifier, ordered role slots, exact model identities/revisions, canonical
edges, and assigned hard requirements. Equivalent candidates merge their
provenance and evidence-reference collections using sorted set union; no
source reference is discarded.

Enumeration is lazy and stops after observing the first unique candidate past
the configured emission cap. The result records:

- configured node and candidate caps;
- emitted valid and rejected counts;
- whether enumeration completed;
- whether truncation occurred;
- the deterministic truncation reason;
- the canonical order definition; and
- when truncated, a lower bound showing that at least `cap + 1` unique
  candidates existed.

The engine does not claim an exact total when enumeration stopped early.
Truncation by canonical order is reproducibility behavior only and carries no
preference or recommendation meaning.

## Baseline Roles

The only certified roles are:

- `PRIMARY`: owns the main workload transformation or generation requirement;
- `SPECIALIST`: satisfies an explicit specialized capability partition;
- `VERIFIER`: checks an explicit result invariant or validation requirement;
- `CRITIC`: produces an explicit critique artifact for a downstream consumer;
- `RETRIEVAL_AUGMENTER`: supplies retrieval-derived context;
- `TOOL_MODEL`: supplies an explicitly required tool or code-related result.

Role names do not imply capabilities. Each role slot carries explicit hard
requirements evaluated through Phase 4 contracts. For example,
`RETRIEVAL_AUGMENTER` requires declared retrieval support, while a
`TOOL_MODEL` requires the specific tool, structured-argument, result-consumer,
or code capability demanded by the graph. `VERIFIER` and `CRITIC` receive
requirements derived from explicit validation or critique stages; their role
names cannot manufacture reasoning or quality claims.

## Certified Baseline Topologies

The only certified topology shapes are:

1. `SINGLE`: `PRIMARY`
2. `PRIMARY_VERIFIER`: `PRIMARY -> VERIFIER`
3. `PRIMARY_CRITIC`: `PRIMARY -> CRITIC`
4. `PRIMARY_SPECIALIST_PRIMARY`:
   `PRIMARY -> SPECIALIST -> PRIMARY`
5. `PRIMARY_RETRIEVAL_PRIMARY`:
   `PRIMARY -> RETRIEVAL_AUGMENTER -> PRIMARY`
6. `PRIMARY_TOOL_PRIMARY`: `PRIMARY -> TOOL_MODEL -> PRIMARY`
7. `PRIMARY_SPECIALIST_VERIFIER`:
   `PRIMARY -> SPECIALIST -> VERIFIER`

Every arrow represents a directed logical handoff. The two `PRIMARY` stages in
a return topology have distinct stage identifiers but must reference the same
exact provider, model ID, family, and revision. This prevents a repeated role
from silently substituting a different primary model.

The topology library rejects all other shapes in the certified baseline,
including cycles, recursive expansion, self-calling loops, self-edges, orphan
nodes, disconnected stages, backward edges, and unsupported role transitions.

## Pattern Applicability Rules

Templates are considered only when certified inputs justify their roles:

- `SINGLE` applies when one exact Phase 4 record can satisfy all assigned hard
  model requirements.
- `PRIMARY_VERIFIER` applies only when the graph includes an explicit logical
  verification or validation requirement after primary output.
- `PRIMARY_CRITIC` applies only when an explicit critique artifact is required
  and consumed by the declared output path.
- `PRIMARY_SPECIALIST_PRIMARY` applies only when an explicit specialized
  capability must feed back into the same primary model.
- `PRIMARY_RETRIEVAL_PRIMARY` applies only when retrieval is required and its
  context must return to the primary stage.
- `PRIMARY_TOOL_PRIMARY` applies only when an explicit tool or code result must
  return to the primary stage.
- `PRIMARY_SPECIALIST_VERIFIER` applies only when an explicit specialized
  result must subsequently be verified.

The engine may instantiate every applicable pattern. Applicability is a hard
rule, not a preference. A pattern is not included merely to increase candidate
count.

## Data Flow

```text
Certified Phase 2 workload requirements
                  +
Ready Phase 3 logical ExecutionGraph
                  +
Phase 4 registry, compatibility, discovery, and evidence
                  |
                  v
        Input and identity validation
                  |
                  v
        Certified pattern applicability
                  |
                  v
   Deterministic exact-record instantiation
                  |
                  v
 Independent structural/capability/handoff/evidence validation
                  |
                  v
 Canonical deduplication and bounded emission
                  |
                  v
 Phase 5 result: valid candidates + rejected candidates + truncation metadata
```

No step mutates its inputs. Validation occurs before a candidate enters the
valid collection. Rejected candidates remain visible with their original
structure, provenance, and ordered reasons.

## Handoff Compatibility

Each edge carries a declared logical artifact contract. A handoff is valid only
when:

- the source stage declares an output that satisfies the carried artifact;
- the target stage declares compatible input support;
- the handoff contributes to a complete entry-to-exit path;
- the edge type is allowed for the certified role transition;
- required structured data, tool results, retrieval context, or validation
  artifacts retain their explicit semantics; and
- evidence required for either side is acceptable under the supplied Phase 4
  evidence requirement.

An overlapping generic text modality cannot silently substitute for an
explicit structured output, tool result, retrieval context, image, audio,
video, or other specialized contract. Unknown or undeclared handoff support
fails closed.

## Invariants

Every emitted candidate must satisfy these invariants:

1. The schema version is exactly supported.
2. Candidate and stage identifiers are nonblank and deterministic.
3. Workload, request, session, graph, and registry identities are consistent.
4. Every model identity includes exact provider, model ID, family, and
   revision from one Phase 4 record.
5. Every stage has one certified role and explicit hard requirements.
6. Every stage has nonblank capability justification and provenance.
7. Every edge references existing stages and an allowed transition.
8. The graph is a connected DAG with no self-edge, cycle, orphan, or recursive
   expansion.
9. The topology exactly matches one certified pattern.
10. Repeated `PRIMARY` stages use the same exact model identity and revision.
11. Every assigned hard requirement is covered by an explicit capability.
12. Every handoff has compatible source output and target input contracts.
13. Every required evidence assessment is acceptable and linked to the exact
    capability claim it supports.
14. Provenance references remain complete and immutable.
15. Node count and emitted candidate count remain within certified bounds.
16. A valid candidate contains no ranking, selection, hardware, placement,
    scheduling, optimization, or runtime decision.

Any unresolved hard invariant makes that candidate `REJECTED`.

## Failure Semantics

### Input failure

Malformed or identity-inconsistent upstream input prevents generation and
returns a fail-closed result with ordered input issues. Phase 5 does not repair
or reinterpret uncertified upstream state.

### Independent candidate failure

Candidates are evaluated independently. Failure of one candidate does not
invalidate another candidate. Each rejected candidate retains all original
nodes, edges, model identities, requirements, evidence references, and
deterministic rejection reasons.

### Overall result

- At least one valid candidate produces `READY`, even when other candidates
  are rejected.
- No valid candidate produces `FAIL` when the certified input declares that
  composition is required.
- No candidate produces `NOT_APPLICABLE` only when the certified input
  explicitly declares that no model composition is required.
- Truncation never changes a validated candidate's state. It is separately
  reported and never described as selection or optimization.

Phase 5 never relaxes a hard requirement, substitutes an unknown capability,
promotes weak evidence, repairs a handoff, or invents a fallback candidate.

## Deterministic Behavior

Equivalent logical inputs must produce equivalent outputs. Determinism is
enforced through:

- fixed schema and pattern identifiers;
- canonical role-slot and edge ordering;
- exact Phase 4 identity ordering by provider, model ID, family, and revision;
- stable requirement, evidence-reference, provenance, issue, and rejection
  ordering;
- deterministic composition IDs derived from canonical content using a stable
  cryptographic digest;
- online semantic deduplication by canonical signature;
- fixed certified maxima and explicit smaller caller bounds; and
- no timestamps, random UUIDs, Python `hash()`, environment values, filesystem
  paths, unordered set iteration, or machine-specific inputs in decisions.

The same input may be evaluated repeatedly without changing source workload,
graph, registry, model records, evidence, patterns, candidate drafts, or
results.

## Provenance Model

Every candidate links to, rather than rewrites:

- Phase 2 workload intelligence identity and evidence;
- Phase 3 graph identity, readiness, node requirements, and graph provenance;
- the Phase 4 registry fingerprint;
- exact Phase 4 capability record identities and revisions;
- Phase 4 compatibility and discovery evidence;
- Phase 4 capability evidence assessments used by hard evidence constraints;
- the certified pattern identifier and version; and
- deterministic instantiation and validation reasons.

References must be nonblank, immutable, and deterministically ordered. Missing
required provenance rejects the affected candidate. Deduplication merges
provenance references but never drops or fabricates them.

## Testing Strategy

All implementation tasks use contracts-first TDD. Tests use immutable real
contracts and deterministic fixtures; no network, model invocation, hardware,
scheduler, or runtime dependency is permitted.

### Contract tests

Test valid minimal and full candidates, every role and validity state, exact
identity/version preservation, nonblank evidence, deterministic serialization,
collection immutability, forbidden fields, invalid identities, dangling edges,
self-edges, cycles, orphans, and certified bounds.

### Pattern-library tests

Test every certified topology exactly, repeated-primary identity constraints,
allowed transitions, invalid transitions, unknown roles, topology mutation,
recursive/cyclic shapes, and deterministic pattern enumeration.

### Instantiation tests

Test every applicability rule, exact Phase 4 compatibility reuse, single and
multi-model bindings, absence of raw-text guessing, exact identity propagation,
no capability inference, deterministic IDs, input immutability, and zero/one/
many candidate outcomes.

### Validation tests

Test structural validity, capability coverage, handoff contracts, evidence
requirements, identity/version consistency, provenance completeness, issue
ordering, independent candidate rejection, and absence of automatic repairs.

### Deduplication and bound tests

Test semantic duplicate collapse, provenance union, nonduplicate preservation,
three-node enforcement, configurable smaller bounds, the 256-candidate maximum,
lazy truncation detection, lower-bound metadata, deterministic output, and the
absence of preference meaning in canonical order.

### Integration and adversarial tests

Test the complete Phase 2-to-Phase 5 flow, malformed upstream contracts,
identity drift, registry conflicts, weak or conflicting evidence, unsupported
handoffs, invalid role transitions, cycles, recursion attempts, candidate
explosion, partial candidate failure, zero-valid-candidate failure, nested
boundary leakage, and immutability of every source artifact.

### Certification tests

Machine-readable Phase 5 certification must require gates for contracts,
patterns, instantiation, validation, deduplication/bounds, integration
hardening, identity, provenance, determinism, fail-closed behavior, boundary
compliance, full regression, and documentation. Certification passes only when
every required gate passes with nonblank evidence and no unresolved violation.

## Task Breakdown

### Task 1: Composition Contract Baseline

Define immutable versioned contracts for roles, pattern identifiers, stage
nodes, handoff edges, candidates, validity, rejection reasons, generation
metadata, and overall result. Enforce basic identity, collection, DAG, evidence,
and phase-boundary invariants without implementing generation.

### Task 2: Certified Pattern Library

Encode exactly the seven certified topology definitions. Validate role slots,
transitions, repeated-primary constraints, connectivity, acyclicity, maximum
three-node size, deterministic enumeration, and immutability. Do not bind model
records yet.

### Task 3: Candidate Instantiation Engine

Derive per-role hard requirements from certified workload and graph artifacts,
reuse Phase 4 compatibility/discovery/evidence results, bind exact records to
applicable pattern slots, and create deterministic candidate drafts. Do not
validate away or rank candidates.

### Task 4: Composition Validation Engine

Independently validate every draft for certified structure, capability
coverage, handoff compatibility, evidence consistency, identity/version
consistency, provenance, determinism, and boundary compliance. Emit `VALID` or
`REJECTED` candidates with deterministic reasons and no repair behavior.

### Task 5: Candidate Deduplication & Bounded Generation

Implement canonical semantic signatures, provenance-preserving duplicate
merging, the three-node hard limit, the 256-candidate certified maximum,
smaller caller limits, lazy bounded enumeration, and transparent truncation
metadata. Canonical ordering must remain explicitly non-preferential.

### Task 6: Integration & Failure Hardening

Stress the complete Phase 5 lifecycle with malformed, conflicting, cyclic,
recursive, unsupported, evidence-invalid, identity-inconsistent, and
boundary-leaking states. Prove independent candidate failure, zero-valid
failure, source immutability, and absence of ranking, selection, hardware,
placement, scheduling, optimization, or runtime behavior.

### Task 7: Phase 5 Certification

Create the machine-readable certification configuration and evaluator for the
complete Phase 5 baseline. Require every locked gate, complete nonblank
evidence, deterministic results, passing regression evidence, documentation,
and zero unresolved boundary violations.

## Certification Exit Criteria

Phase 5 is certifiable only when:

1. all seven tasks are implemented and independently verified;
2. all seven certified patterns are represented exactly;
3. candidates are immutable, deterministic, explainable, and provenance-rich;
4. structural, capability, handoff, evidence, and identity validation pass or
   fail closed per candidate;
5. deduplication and generation remain within the locked hard bounds;
6. partial candidate failure cannot erase valid candidates;
7. composition-required workloads fail when no valid candidate remains;
8. no ranking, scoring, selection, graph assignment, optimization, hardware,
   placement, scheduling, runtime, recursion, or swarm behavior exists;
9. focused and full regression suites pass; and
10. every Phase 5 certification gate passes with nonblank evidence.

Implementation planning and Phase 5 Task 1 begin only under a separate locked
request. This design task creates no production code or tests.
