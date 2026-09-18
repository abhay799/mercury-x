import { CONTROL_CENTER_SCHEMA } from '../types.js';

const provenance = (sourceType, evidenceState, calibrationState, ...sourceIds) => ({
  sourceType,
  generatedAt: '2026-09-18T00:00:00Z',
  evidenceState,
  calibrationState,
  sourceIds,
});

const staticDemo = (...ids) => provenance('STATIC DEMO', 'VERIFIED', 'NOT_APPLICABLE', ...ids);
const synthetic = (...ids) => provenance('SYNTHETIC', 'VERIFIED', 'SYNTHETIC_FIXTURE', ...ids);
const simulated = (...ids) => provenance('SIMULATED', 'PARTIAL', 'UNCALIBRATED', ...ids);
const unknown = (...ids) => provenance('UNKNOWN', 'UNKNOWN', 'UNCALIBRATED', ...ids);

const data = {
  schema: CONTROL_CENTER_SCHEMA,
  mode: 'STATIC DEMONSTRATION',
  generatedAt: '2026-09-18T00:00:00Z',
  notice: 'Control-plane demonstration. No production infrastructure is connected.',
  overview: {
    metrics: [
      { label: 'Tracked workloads', value: '4', detail: '2 ready · 1 deferred · 1 unknown', provenance: staticDemo('demo-workloads') },
      { label: 'Hard invariants', value: '10 / 10', detail: 'No weakened constraints', provenance: synthetic('safety-fixture') },
      { label: 'Certified phases', value: '0–30', detail: 'Internal executable gates', provenance: staticDemo('certification-manifests') },
      { label: 'Authoritative executors', value: '1', detail: 'Migration invariant held', provenance: simulated('migration-scenario-07') },
    ],
    signals: [
      { label: 'Quality floor', value: '0.92', state: 'PROTECTED', provenance: synthetic('slo-demo-014') },
      { label: 'Placement generation', value: '42', state: 'CURRENT', provenance: synthetic('placement-demo-042') },
      { label: 'Twin calibration', value: 'UNCALIBRATED', state: 'ADVISORY', provenance: simulated('twin-scenario-03') },
      { label: 'Policy promotion', value: 'HUMAN REVIEW', state: 'BLOCKED', provenance: staticDemo('policy-candidate-08') },
    ],
  },
  workloads: [
    { id: 'wrk-7f2a', name: 'Document reasoning', modality: 'TEXT', state: 'READY', qualityFloor: '0.92', placement: 'edge-a / candidate-03', slo: 'slo-v6', model: 'atlas-reasoner / r17', precision: 'BF16', reasoningBudget: 'rb-410', negotiation: 'ACCEPT', provenance: synthetic('gateway-request-7f2a', 'slo-v6') },
    { id: 'wrk-91cd', name: 'Vision verification', modality: 'IMAGE + TEXT', state: 'READY', qualityFloor: '0.95', placement: 'core-b / candidate-11', slo: 'slo-v4', model: 'prism-vision / r8', precision: 'FP16', reasoningBudget: 'rb-411', negotiation: 'ACCEPT', provenance: synthetic('gateway-request-91cd', 'slo-v4') },
    { id: 'wrk-a104', name: 'Private retrieval', modality: 'STRUCTURED DATA', state: 'DEFER', qualityFloor: '0.90', placement: 'awaiting eligible domain', slo: 'slo-v2', model: 'unassigned', precision: 'unassigned', reasoningBudget: 'rb-412', negotiation: 'DEFER', provenance: staticDemo('privacy-envelope-22', 'federation-snapshot-9') },
    { id: 'wrk-c882', name: 'Long-context synthesis', modality: 'MULTIMODAL', state: 'UNKNOWN', qualityFloor: '0.94', placement: 'none', slo: 'slo-v1', model: 'unassigned', precision: 'unassigned', reasoningBudget: 'pending evidence', negotiation: 'UNKNOWN', provenance: unknown('missing-context-evidence') },
  ],
  graph: {
    graphId: 'graph-wrk-7f2a-v3',
    nodes: [
      { id: 'input', label: 'Canonical input', type: 'INPUT', state: 'VERIFIED', model: '—', placement: 'gateway', context: 'session-18' },
      { id: 'retrieve', label: 'Retrieve context', type: 'RETRIEVAL', state: 'READY', model: 'retrieval capability', placement: 'edge-a', context: 'project-scope' },
      { id: 'reason', label: 'Reason', type: 'REASONING', state: 'READY', model: 'atlas-reasoner r17', placement: 'candidate-03', context: 'kv-ref-61' },
      { id: 'verify', label: 'Verify output', type: 'VALIDATION', state: 'REQUIRED', model: 'verifier capability', placement: 'candidate-03', context: 'evidence-set-4' },
      { id: 'output', label: 'Structured output', type: 'OUTPUT', state: 'PENDING', model: '—', placement: 'gateway', context: 'session-18' },
    ],
    edges: [['input', 'retrieve'], ['retrieve', 'reason'], ['reason', 'verify'], ['verify', 'output']],
    provenance: synthetic('phase3-graph-fixture', 'workload-profile-7f2a'),
  },
  models: [
    { stage: 'reason', identity: 'atlas-reasoner', revision: 'r17', capability: 'GENERATION · REASONING · TOOL USE', precision: 'BF16', adaptation: 'DEPTH variant d24', quality: '≥ 0.92', calibration: 'UNCALIBRATED', provenance: synthetic('model-registry-31', 'precision-profile-19') },
    { stage: 'verify', identity: 'sentinel-verifier', revision: 'r5', capability: 'VALIDATION · STRUCTURED OUTPUT', precision: 'FP32', adaptation: 'NONE', quality: 'Hard verification required', calibration: 'UNCALIBRATED', provenance: synthetic('model-registry-31', 'composition-profile-07') },
  ],
  memory: {
    session: [
      { scope: 'TURN', records: 6, lifecycle: 'ACTIVE', key: 'current-request', provenance: synthetic('session-memory-demo') },
      { scope: 'TASK', records: 18, lifecycle: 'ACTIVE', key: 'reasoning-trace', provenance: synthetic('session-memory-demo') },
      { scope: 'SESSION', records: 34, lifecycle: 'COMPACTED', key: 'session-summary', provenance: synthetic('compaction-result-4') },
    ],
    global: [
      { namespace: 'PROJECT / mercury-demo', state: 'CURRENT', records: 12, authorization: 'EXACT MATCH', provenance: staticDemo('global-context-demo') },
      { namespace: 'WORKSPACE / research', state: 'CONFLICT REVIEW', records: 3, authorization: 'RESTRICTED', provenance: staticDemo('global-conflict-demo') },
    ],
    cache: { status: 'ELIGIBLE', identity: 'kv-ref-61', compatibility: 'EXACT', provenance: synthetic('semantic-kv-fixture') },
  },
  compute: {
    topologyGeneration: 42,
    nodes: [
      { id: 'edge-a', personality: 'Latency-oriented CPU node', health: 'HEALTHY', utilization: '61%', placements: 2, x: 17, y: 52, provenance: synthetic('hardware-profile-edge-a') },
      { id: 'core-b', personality: 'Accelerator-capable logical profile', health: 'HEALTHY', utilization: '74%', placements: 1, x: 50, y: 22, provenance: synthetic('hardware-profile-core-b') },
      { id: 'core-c', personality: 'High-memory logical profile', health: 'DEGRADED', utilization: '82%', placements: 0, x: 82, y: 54, provenance: simulated('hardware-profile-core-c') },
      { id: 'archive-d', personality: 'Context storage profile', health: 'HEALTHY', utilization: '38%', placements: 1, x: 50, y: 82, provenance: synthetic('hardware-profile-archive-d') },
    ],
    links: [
      { from: 'edge-a', to: 'core-b', state: 'ELIGIBLE', generation: 42 },
      { from: 'core-b', to: 'core-c', state: 'CONSTRAINED', generation: 42 },
      { from: 'core-c', to: 'archive-d', state: 'ELIGIBLE', generation: 42 },
      { from: 'archive-d', to: 'edge-a', state: 'ELIGIBLE', generation: 42 },
    ],
    provenance: synthetic('topology-snapshot-42'),
  },
  slo: {
    contractId: 'slo-v6', qualityFloor: '0.92', confidenceFloor: '0.86', verificationDepth: '2',
    reasoning: { primary: 16, verification: 6, speculation: 4, escalation: 3, aggregation: 2, unit: 'logical units' },
    resourceRequest: '31 logical compute units', negotiation: 'ACCEPT', protected: ['QUALITY', 'VERIFICATION', 'SAFETY', 'PRIVACY', 'AUTHORIZATION', 'RESIDENCY'],
    provenance: synthetic('metric-registry-v4', 'reasoning-budget-410', 'compute-offer-12'),
  },
  migration: {
    migrationId: 'migration-scenario-07', generation: 7, fingerprint: 'sha256:8c1d…a702', state: 'VERIFY',
    authority: { source: 'PROVISIONAL', destination: 'NOT AUTHORITATIVE', authoritativeCount: 1 },
    stages: [
      ['Source', 'COMPLETE'], ['Trigger', 'COMPLETE'], ['Eligibility', 'COMPLETE'], ['Destination', 'COMPLETE'],
      ['Checkpoint', 'COMPLETE'], ['Transfer', 'COMPLETE'], ['Restore', 'COMPLETE'], ['Verify', 'ACTIVE'],
      ['Cutover', 'PENDING'], ['Retire', 'PENDING'],
    ],
    preserved: ['Model/version', 'Precision', 'Graph position', 'Session/context', 'KV references', 'Verification state', 'Reasoning budget', 'Placement provenance', 'Topology generation', 'SLO contract', 'Scheduler ownership', 'Speculation state', 'Authorization'],
    rollback: 'Armed: source remains authoritative until verified cutover',
    provenance: simulated('phase21-control-scenario', 'checkpoint-07'),
  },
  healing: {
    state: 'DIAGNOSE', trigger: 'DEGRADATION', decision: 'Candidate heal-03 preserves all hard constraints', verification: 'REQUIRED',
    steps: [['Detect', 'COMPLETE'], ['Diagnose', 'ACTIVE'], ['Recovery decision', 'PENDING'], ['Safe action', 'PENDING'], ['Verify', 'PENDING'], ['Resume / Escalate', 'PENDING']],
    provenance: simulated('phase22-control-scenario'),
  },
  scheduler: {
    challenges: [
      { id: 'challenge-14', risk: 'Starvation under priority pressure', outcome: 'DETECTED', severity: 'HIGH', provenance: synthetic('adversarial-scenario-14') },
      { id: 'challenge-15', risk: 'Stale topology admission', outcome: 'REJECTED', severity: 'CRITICAL', provenance: synthetic('adversarial-scenario-15') },
    ],
    alternatives: [
      { id: 'cf-28a', scenario: 'Defer workload until eligible residency domain', outcome: 'VALID', uncertainty: '0.34', provenance: simulated('counterfactual-28a') },
      { id: 'cf-28b', scenario: 'Lower quality to fit current capacity', outcome: 'INVALID', uncertainty: '—', provenance: simulated('counterfactual-28b') },
    ],
    policy: { id: 'policy-candidate-08', stage: 'HUMAN APPROVAL', path: ['OFFLINE', 'SHADOW', 'CANARY', 'HUMAN APPROVAL', 'PROMOTION'], promoted: false, provenance: staticDemo('policy-evaluation-08') },
  },
  federation: {
    domains: [
      { id: 'domain-edge-in', class: 'EDGE', residency: 'IN', authorization: 'ELIGIBLE', state: 'AVAILABLE', provenance: synthetic('federation-domain-1') },
      { id: 'domain-core-eu', class: 'CLOUD', residency: 'EU', authorization: 'DENIED', state: 'EXCLUDED', provenance: synthetic('federation-domain-2') },
      { id: 'domain-lab', class: 'RESEARCH', residency: 'IN', authorization: 'RESTRICTED', state: 'ADVISORY', provenance: staticDemo('federation-domain-3') },
    ],
    privacy: { classification: 'CONFIDENTIAL', purpose: 'DOCUMENT ANALYSIS', residency: 'IN', access: 'MINIMUM NECESSARY', logging: 'REDACTED', failClosed: true, provenance: synthetic('privacy-envelope-22') },
  },
  twin: {
    scenarioId: 'twin-scenario-03', title: 'Core node degradation with queue surge', calibration: 'UNCALIBRATED', status: 'ADVISORY',
    inputs: ['Synthetic topology generation 42', 'Simulated +30% arrival pressure', 'Hypothetical loss of core-c'],
    alternatives: [
      { action: 'Defer low-priority batch work', effect: 'Queue pressure decreases in simulation', confidence: 'UNKNOWN' },
      { action: 'Preserve critical placements and quality floors', effect: 'Hard constraints remain satisfied', confidence: 'PARTIAL' },
      { action: 'Lower quality floor', effect: 'Rejected by safety invariant', confidence: 'NOT APPLICABLE' },
    ],
    provenance: simulated('twin-fixture-03'),
  },
  governance: {
    pipeline: ['Evidence', 'Authority', 'Safety invariants', 'Decision', 'Human escalation', 'Execution authorization', 'Verification'],
    decisions: [
      { id: 'control-301', objective: 'Preserve quality during capacity pressure', state: 'HUMAN REVIEW', authority: 'operator-group-a', outcome: 'ESCALATE', provenance: staticDemo('control-objective-301') },
      { id: 'control-302', objective: 'Reject stale placement generation', state: 'VERIFIED', authority: 'system invariant', outcome: 'REJECT', provenance: synthetic('control-objective-302') },
      { id: 'control-303', objective: 'Authorize cross-domain execution', state: 'UNKNOWN', authority: 'insufficient', outcome: 'DEFER', provenance: unknown('missing-domain-authority') },
    ],
  },
  evidence: [
    { id: 'decision-7f2a', workload: 'wrk-7f2a', timestamp: '2026-09-18 00:00:14Z', source: 'placement-demo-042', evidence: 'VERIFIED', policy: 'placement-policy-v3', authority: 'control-plane', action: 'Candidate eligible', verification: 'PASS', outcome: 'ACCEPT', provenance: synthetic('placement-demo-042') },
    { id: 'decision-a104', workload: 'wrk-a104', timestamp: '2026-09-18 00:00:18Z', source: 'privacy-envelope-22', evidence: 'VERIFIED', policy: 'residency-policy-v2', authority: 'namespace-policy', action: 'No eligible domain', verification: 'PASS', outcome: 'DEFER', provenance: staticDemo('privacy-envelope-22') },
    { id: 'decision-c882', workload: 'wrk-c882', timestamp: '2026-09-18 00:00:21Z', source: 'missing-context-evidence', evidence: 'UNKNOWN', policy: 'fail-closed-v1', authority: 'insufficient', action: 'No action', verification: 'NOT RUN', outcome: 'UNKNOWN', provenance: unknown('missing-context-evidence') },
  ],
  system: {
    phaseRange: '0–30', regression: '1506 passed (previous verified baseline)', mode: 'RESEARCH / STATIC DEMO', backend: 'Disconnected provider boundary',
    claims: [
      ['Control-plane logic', 'IMPLEMENTED'], ['Synthetic fixtures', 'AVAILABLE'], ['Counterfactual and twin output', 'SIMULATED / ADVISORY'],
      ['Production infrastructure adapters', 'NOT CONNECTED'], ['Real GPU live migration', 'NOT CLAIMED'], ['Autonomous policy promotion', 'FORBIDDEN'],
    ],
    provenance: staticDemo('repository-head-8bbe0f8', 'phase-certification-manifests'),
  },
};

const deepFreeze = (value) => {
  if (value && typeof value === 'object' && !Object.isFrozen(value)) {
    Object.freeze(value);
    Object.values(value).forEach(deepFreeze);
  }
  return value;
};

export const DEMO_DATA = deepFreeze(data);
