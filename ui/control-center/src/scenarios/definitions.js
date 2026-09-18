import { deepFreeze, SCENARIO_SCHEMA, validateScenarioCatalog } from './contracts.js';

export const REQUIRED_SCENARIO_IDS = Object.freeze([
  'normal-orchestration',
  'quality-slo-conflict',
  'live-migration',
  'self-healing',
  'adversarial-counterfactual',
  'federated-privacy',
]);

const provenance = (sourceType, evidenceState, calibrationState, ...sourceIds) => ({
  sourceType, generatedAt: 'LOGICAL-EPOCH-2026-09-18', evidenceState, calibrationState, sourceIds,
});
const synthetic = (...ids) => provenance('SYNTHETIC', 'VERIFIED', 'SYNTHETIC_FIXTURE', ...ids);
const simulated = (...ids) => provenance('SIMULATED', 'PARTIAL', 'UNCALIBRATED', ...ids);
const staticDemo = (...ids) => provenance('STATIC DEMO', 'VERIFIED', 'NOT_APPLICABLE', ...ids);
const unknown = (...ids) => provenance('UNKNOWN', 'UNKNOWN', 'UNCALIBRATED', ...ids);

function makeStep(scenarioId, workloadId, sequence, label, status, route, details = {}) {
  const logicalTime = `T+${String((sequence - 1) * 10).padStart(3, '0')}`;
  const stepProvenance = details.provenance ?? synthetic(`${scenarioId}-step-${sequence}`);
  const decision = details.decision ?? label.toUpperCase().replace(/[^A-Z0-9]+/g, '_');
  const event = {
    eventId: `evt:${scenarioId}:${String(sequence).padStart(2, '0')}`,
    scenarioId, workloadId, logicalTime, decision,
    evidence: details.evidence ?? `${scenarioId}-evidence-${sequence}`,
    authority: details.authority ?? 'mercury-control-plane',
    provenance: stepProvenance,
    safetyResult: details.safetyResult ?? 'HARD_INVARIANTS_PRESERVED',
    verificationResult: details.verificationResult ?? 'NOT_REQUIRED',
  };
  return {
    sequence, stepId: `${scenarioId}:${sequence}`, label, logicalTime, status, route,
    decision, evidence: event.evidence, authority: event.authority,
    safetyResult: event.safetyResult, verificationResult: event.verificationResult,
    affectedResources: details.affectedResources ?? [], explanation: details.explanation ?? '',
    provenance: stepProvenance, event, terminal: details.terminal ?? false,
    projection: details.projection ?? {},
  };
}

function scenario(base, stepSpecs) {
  const steps = stepSpecs.map((spec, index) => makeStep(base.scenarioId, base.workloadId, index + 1, ...spec));
  return {
    schema: SCENARIO_SCHEMA,
    sourceType: base.provenance.sourceType,
    calibrationState: base.provenance.calibrationState,
    currentStep: 0,
    status: 'READY',
    evidenceState: base.provenance.evidenceState,
    ...base,
    steps,
  };
}

const normal = scenario({
  scenarioId: 'normal-orchestration', name: 'Normal workload orchestration', workloadId: 'wrk-demo-normal',
  description: 'A canonical workload progresses through every major MERCURY decision boundary and completes after verification.',
  expectedTerminalState: 'ACCEPT', affectedResources: ['gateway', 'edge-a', 'candidate-03'],
  safetyDecisions: ['IDENTITY_PRESERVED', 'QUALITY_FLOOR_PRESERVED', 'AUTHORIZATION_VERIFIED'],
  provenance: synthetic('scenario-normal-v1', 'phase0-20-demo-contracts'),
}, [
  ['Incoming request', 'RUNNING', 'workloads', { explanation: 'The gateway receives a versioned request envelope.', projection: { workloadState: 'ADMITTED' } }],
  ['Gateway normalization', 'RUNNING', 'workloads', { explanation: 'Identity, session, and constraints are canonicalized.' }],
  ['Workload classification', 'RUNNING', 'workloads', { explanation: 'TEXT reasoning workload with structured output is inferred.' }],
  ['Execution graph', 'RUNNING', 'graph', { explanation: 'INPUT → RETRIEVAL → REASONING → VALIDATION → OUTPUT.' }],
  ['Model capability', 'RUNNING', 'models', { explanation: 'Exact model revision satisfies reasoning and validation capabilities.' }],
  ['Precision decision', 'RUNNING', 'models', { explanation: 'Registered BF16 profile remains compatible with quality constraints.' }],
  ['Context resolution', 'RUNNING', 'memory', { explanation: 'Authorized session context and exact KV compatibility are resolved.' }],
  ['Topology evaluation', 'RUNNING', 'compute', { explanation: 'Current topology generation exposes an eligible path.', affectedResources: ['edge-a', 'core-b'] }],
  ['Placement prediction', 'RUNNING', 'compute', { explanation: 'Candidate-03 is eligible; prediction remains a control artifact.' }],
  ['Reasoning budget', 'RUNNING', 'slo', { explanation: 'Reasoning and verification receive bounded logical units.' }],
  ['Intelligence SLO', 'RUNNING', 'slo', { explanation: 'Quality floor 0.92 and verification depth 2 are protected.' }],
  ['Compute agreement', 'RUNNING', 'slo', { explanation: 'An exact feasible offer is accepted without constraint changes.' }],
  ['Execution authorization', 'RUNNING', 'governance', { explanation: 'Authority and current generations pass all hard gates.' }],
  ['Verification', 'RUNNING', 'evidence', { explanation: 'The result passes required verification.', verificationResult: 'PASS' }],
  ['Successful completion', 'ACCEPT', 'overview', { explanation: 'The workload completes with all hard invariants preserved.', verificationResult: 'PASS', terminal: true, projection: { workloadState: 'COMPLETE', negotiation: 'ACCEPT' } }],
]);

const qualityConflict = scenario({
  scenarioId: 'quality-slo-conflict', name: 'Quality / SLO conflict', workloadId: 'wrk-demo-quality',
  description: 'Resource pressure proposes an invalid cheaper path; MERCURY rejects degradation and issues an explicit counteroffer.',
  expectedTerminalState: 'COUNTEROFFER', requestedQualityFloor: '0.92', preservedQualityFloor: '0.92', availableResourceUnits: 18, requestedResourceUnits: 31,
  affectedResources: ['candidate-03', 'resource-envelope-18'],
  safetyDecisions: ['QUALITY_DEGRADATION_REJECTED', 'VERIFICATION_DEPTH_PRESERVED', 'EXPLICIT_APPROVAL_REQUIRED'],
  provenance: synthetic('scenario-quality-v1', 'slo-v6', 'reasoning-budget-410'),
}, [
  ['Quality request received', 'RUNNING', 'slo', { explanation: 'The request requires quality floor 0.92 and verification depth 2.' }],
  ['Resource envelope evaluated', 'RUNNING', 'compute', { explanation: 'Only 18 of 31 requested logical units are currently represented.' }],
  ['Cheaper path proposed', 'RUNNING', 'slo', { explanation: 'A hypothetical lower-quality path is inspected, not accepted.', provenance: simulated('quality-conflict-alternative') }],
  ['Hard conflict detected', 'REJECT', 'slo', { explanation: 'The proposed path would violate the quality floor.', safetyResult: 'QUALITY_DEGRADATION_REJECTED' }],
  ['Silent degradation refused', 'REJECT', 'governance', { explanation: 'Quality and verification remain protected.', safetyResult: 'HARD_INVARIANT_ENFORCED' }],
  ['Additional resources requested', 'DEFER', 'compute', { explanation: 'The control plane requests a compatible resource envelope.' }],
  ['Counteroffer issued', 'COUNTEROFFER', 'slo', { explanation: 'The offer changes only negotiable resource/wait constraints and requires explicit approval.', terminal: true, projection: { workloadState: 'COUNTEROFFER', negotiation: 'COUNTEROFFER', qualityConflict: true } }],
]);

const migration = scenario({
  scenarioId: 'live-migration', name: 'Live workload migration', workloadId: 'wrk-demo-migration',
  description: 'MERCURY orchestrates a simulated control-plane migration from Node A to Node B with verified cutover and rollback protection.',
  expectedTerminalState: 'ACCEPT', authoritativeExecutorCount: 1, affectedResources: ['node-a', 'node-b'],
  rollbackPath: ['Verification or cutover failure', 'Rollback to source checkpoint', 'Restore Node A as sole authority'],
  safetyDecisions: ['AUTHORITY_NOT_EXPANDED', 'EXACTLY_ONE_AUTHORITATIVE_EXECUTOR', 'ROLLBACK_ARMED'],
  provenance: simulated('scenario-migration-v1', 'phase21-control-contracts'),
}, [
  ['Running on Node A', 'RUNNING', 'migration', { explanation: 'Node A is the sole authoritative executor.', affectedResources: ['node-a'] }],
  ['Degradation trigger', 'RUNNING', 'compute', { explanation: 'A synthetic placement-health trigger is recorded.', affectedResources: ['node-a'], provenance: simulated('node-a-degradation') }],
  ['Migration eligibility', 'RUNNING', 'migration', { explanation: 'Agreement, authorization, and source generations are current.' }],
  ['Destination qualification', 'RUNNING', 'compute', { explanation: 'Node B matches topology, placement, authorization, and SLO requirements.', affectedResources: ['node-b'] }],
  ['Execution-state checkpoint', 'RUNNING', 'migration', { explanation: 'Model, precision, graph, context, reasoning, SLO, and authority references are sealed.' }],
  ['State / context transfer', 'RUNNING', 'migration', { explanation: 'Control-plane checkpoint and context references are transferred; no physical GPU memory transfer is claimed.' }],
  ['Restore on Node B', 'RUNNING', 'migration', { explanation: 'Node B is restored provisionally and is not yet authoritative.', affectedResources: ['node-b'] }],
  ['Equivalence verification', 'RUNNING', 'migration', { explanation: 'Restored identity, context, budgets, constraints, and security state match.', verificationResult: 'PASS' }],
  ['Atomic cutover', 'RUNNING', 'migration', { explanation: 'Authority changes atomically while retaining exactly one executor.', projection: { migrationAuthority: 'node-b' } }],
  ['Retire Node A authority', 'RUNNING', 'migration', { explanation: 'Node A can no longer commit authoritative output.', affectedResources: ['node-a'] }],
  ['Migration verified', 'ACCEPT', 'migration', { explanation: 'Node B is sole authority; rollback evidence remains inspectable.', verificationResult: 'PASS', terminal: true, projection: { workloadState: 'RUNNING', migrationComplete: true } }],
]);

const healing = scenario({
  scenarioId: 'self-healing', name: 'Self-healing failure recovery', workloadId: 'wrk-demo-healing',
  description: 'A bounded safe recovery preserves quality, privacy, authorization, and SLO constraints and requires post-action verification.',
  expectedTerminalState: 'ACCEPT', affectedResources: ['core-c', 'recovery-candidate-03'],
  alternateVerificationFailurePath: ['VERIFICATION_FAILED', 'ROLLBACK_SAFE_STATE', 'ESCALATE'],
  safetyDecisions: ['QUALITY_PRESERVED', 'AUTHORIZATION_PRESERVED', 'PRIVACY_PRESERVED', 'POST_ACTION_VERIFICATION_REQUIRED'],
  provenance: simulated('scenario-healing-v1', 'phase22-control-contracts'),
}, [
  ['Degradation detected', 'RUNNING', 'compute', { explanation: 'Synthetic health evidence identifies a degraded logical node.', affectedResources: ['core-c'] }],
  ['Evidence collected', 'RUNNING', 'evidence', { explanation: 'Current detection, topology, placement, scheduler, SLO, agreement, and authority generations are collected.' }],
  ['Recovery options evaluated', 'RUNNING', 'migration', { explanation: 'Unsafe candidates that weaken hard constraints are rejected.' }],
  ['Safe recovery selected', 'RUNNING', 'migration', { explanation: 'Candidate heal-03 is reversible and preserves hard constraints.' }],
  ['Action authorized', 'RUNNING', 'governance', { explanation: 'Existing authority permits the bounded recovery; no authority expansion occurs.' }],
  ['Recovery applied', 'RUNNING', 'migration', { explanation: 'The scenario advances logical recovery state only.' }],
  ['Post-action verification', 'RUNNING', 'evidence', { explanation: 'Recovery evidence is checked before resume.', verificationResult: 'PASS' }],
  ['Resume verified workload', 'ACCEPT', 'overview', { explanation: 'The workload resumes only after verification. The failure branch would roll back and ESCALATE.', verificationResult: 'PASS', terminal: true, projection: { workloadState: 'RUNNING', healingComplete: true } }],
]);

const adversarial = scenario({
  scenarioId: 'adversarial-counterfactual', name: 'Adversarial scheduling + counterfactual', workloadId: 'wrk-demo-scheduler',
  description: 'An initially plausible scheduling decision is challenged for starvation and stale evidence; alternatives remain advisory.',
  expectedTerminalState: 'DEFER', executionAuthorized: false, calibrationState: 'UNCALIBRATED', affectedResources: ['queue-critical', 'queue-batch'],
  safetyDecisions: ['STALE_DECISION_REJECTED', 'COUNTERFACTUAL_ADVISORY_ONLY', 'NO_DIRECT_EXECUTION'],
  provenance: simulated('scenario-adversarial-v1', 'phase23-24-control-contracts'),
}, [
  ['Initial decision', 'RUNNING', 'scheduler', { explanation: 'A scheduling artifact appears valid against its original queue snapshot.' }],
  ['Adversarial challenge', 'RUNNING', 'scheduler', { explanation: 'The challenge detects starvation pressure and a stale topology generation.' }],
  ['Current decision rejected', 'REJECT', 'scheduler', { explanation: 'Stale evidence cannot authorize execution.', safetyResult: 'STALE_DECISION_REJECTED' }],
  ['Alternatives simulated', 'RUNNING', 'twin', { explanation: 'Counterfactual options are SIMULATED, ADVISORY, and UNCALIBRATED.', provenance: simulated('counterfactual-set-23') }],
  ['Advisory comparison', 'RUNNING', 'scheduler', { explanation: 'Alternatives compare fairness and hard-constraint preservation without execution.' }],
  ['Safer recommendation', 'DEFER', 'scheduler', { explanation: 'Refresh evidence and defer affected work; no action is directly executed.', terminal: true, projection: { workloadState: 'DEFER', schedulerChallenge: true } }],
]);

const federated = scenario({
  scenarioId: 'federated-privacy', name: 'Federated privacy / residency', workloadId: 'wrk-demo-private',
  description: 'Candidate domains are filtered by residency, privacy, authorization, and minimum-necessary access before placement.',
  expectedTerminalState: 'ACCEPT', selectedCandidate: 'domain-edge-in',
  rejectedCandidates: [{ id: 'domain-core-eu', reason: 'RESIDENCY_MISMATCH' }, { id: 'domain-lab', reason: 'AUTHORIZATION_INSUFFICIENT' }],
  affectedResources: ['domain-edge-in', 'domain-core-eu', 'domain-lab'],
  safetyDecisions: ['RESIDENCY_PRESERVED', 'MINIMUM_NECESSARY_ACCESS', 'REDACTED_AUDIT_EVIDENCE'],
  provenance: synthetic('scenario-federation-v1', 'phase26-27-control-contracts'),
}, [
  ['Federation candidates', 'RUNNING', 'federation', { explanation: 'Three exact execution-domain identities are considered.' }],
  ['Privacy envelope', 'RUNNING', 'federation', { explanation: 'CONFIDENTIAL data requires IN residency and minimum-necessary access.' }],
  ['Authorization evaluated', 'RUNNING', 'governance', { explanation: 'Domain authority is evaluated separately from capability.' }],
  ['EU candidate rejected', 'REJECT', 'federation', { explanation: 'domain-core-eu violates the explicit IN residency constraint.', safetyResult: 'RESIDENCY_MISMATCH' }],
  ['Research candidate rejected', 'REJECT', 'federation', { explanation: 'domain-lab lacks sufficient production authority.', safetyResult: 'AUTHORIZATION_INSUFFICIENT' }],
  ['Compliant candidate selected', 'RUNNING', 'federation', { explanation: 'domain-edge-in satisfies capability, residency, privacy, and authority.' }],
  ['Redacted evidence recorded', 'RUNNING', 'evidence', { explanation: 'The audit event exposes the reason without disclosing protected content.' }],
  ['Privacy-safe placement accepted', 'ACCEPT', 'federation', { explanation: 'Placement is authorized with the privacy envelope preserved.', verificationResult: 'PASS', terminal: true, projection: { workloadState: 'READY', federationCandidate: 'domain-edge-in' } }],
]);

export const SCENARIOS = deepFreeze(validateScenarioCatalog([
  normal, qualityConflict, migration, healing, adversarial, federated,
]));

export { validateScenarioCatalog } from './contracts.js';
