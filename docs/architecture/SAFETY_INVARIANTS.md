# MERCURY X Safety Invariants

These invariants summarize cross-phase rules enforced by contracts, validators, lifecycle engines, tests, and executable certification gates. They are software architecture invariants, not a substitute for operational security review or external certification.

## Quality

MERCURY X must not automatically lower an explicit quality or confidence floor to satisfy compute, latency, queue, placement, migration, or negotiation pressure. A negotiable change must remain explicit and must not alter protected quality or verification requirements.

## Safety and Verification

Verification requirements are hard constraints. Speculative results, migration restoration, and healing actions do not become authoritative until their required verification succeeds. Missing verification is not success.

## Authorization

No migration, healing, federation, memory promotion, retrieval, negotiation, control, or policy decision may gain authority beyond its inputs. Authorization is bound to exact scopes and artifacts. Silence, timeout, confidence, or simulation output is never authorization.

## Privacy, Purpose, and Residency

Privacy scope, data classification, permitted purpose, and residency constraints may be preserved or strengthened, never silently weakened. Cross-session, cross-namespace, or cross-domain access requires an explicit certified boundary and matching authority.

## SLO Integrity

Hard SLO requirements survive compilation, scheduling, negotiation, migration, healing, federation, and platform composition. A phase cannot reinterpret an unsatisfied hard objective as a soft preference.

## Stale State

Generation, version, fingerprint, lease, topology, resource-snapshot, and lineage mismatches must reject, defer, expire, or trigger reevaluation. A decision made against stale state cannot silently continue as current.

## Provenance and Identity

Material artifacts preserve the source identities and evidence needed to validate them. Where content-addressed identity is used, changed logical content must change the fingerprint. Provenance must not be fabricated, blank, or detached from the decision it supports.

## Unknown Evidence

Unknown, incomplete, contradictory, unsupported, or uncalibrated evidence cannot become implicit PASS, admission, approval, placement certainty, promotion, or execution authority. The resulting state remains explicit and fail-closed.

## Bounded Generation

Composition, precision, morphing, retrieval, context, speculation, and other enumerated candidate spaces obey certified limits. Truncation is disclosed and canonical order must not be disguised as ranking or preference.

## Simulation

Counterfactual and datacenter-twin outputs are advisory. Simulation cannot directly reserve resources, mutate production state, authorize execution, promote a policy, or claim measured accuracy without empirical calibration evidence.

## Policy Evolution

There is no autonomous production policy promotion. Candidates progress through controlled states, evaluation evidence, and explicit human approval. Rollback is preserved as a governed action.

## Migration

Migration must preserve workload, context, authorization, SLO, and execution identity across checkpoint, transfer, restore, verification, and cutover. After cutover there is exactly one authoritative executor. Failed verification cannot silently produce a successful cutover.

## Recovery

Self-healing actions are bounded, generation-aware, and ledgered. Recovery must preserve hard constraints and authority, and it requires post-action verification before being treated as successful.

## Speculative Execution

Speculation is bounded. Every branch remains tied to its plan and candidate provenance. Only a verified successful result may commit, exactly one branch is authoritative, and losing branches are cancelled or discarded.

## Human Control

Explicit approval is required for protected operational boundaries, including negotiated changes where approval is required and production policy promotion. Approval binds to the exact artifact, accepted changes, authority, and current generation.

## Research and Production Modes

Research mode may expose controlled experiments and simulations, but it cannot weaken production quality, privacy, authorization, safety, verification, or human-control guarantees. Evidence categories must remain accurately labeled.

