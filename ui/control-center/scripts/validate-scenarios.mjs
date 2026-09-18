import assert from 'node:assert/strict';

import { DemoControlCenterProvider } from '../src/data/demo-provider.js';
import { ScenarioController } from '../src/scenarios/controller.js';
import { REQUIRED_SCENARIO_IDS, SCENARIOS, validateScenarioCatalog } from '../src/scenarios/definitions.js';
import { ScenarioControlCenterProvider } from '../src/scenarios/scenario-provider.js';

assert.equal(SCENARIOS.length, 6, 'all six required scenarios must exist');
assert.deepEqual(SCENARIOS.map((scenario) => scenario.scenarioId).sort(), [...REQUIRED_SCENARIO_IDS].sort());
validateScenarioCatalog(SCENARIOS);

const serialized = JSON.stringify(SCENARIOS);
assert.ok(!serialized.includes('"sourceType":"LIVE"'), 'scenario catalog must not emit LIVE provenance');
assert.ok(!serialized.includes('AUTO_DEGRADE'), 'scenario catalog must prohibit automatic degradation');

for (const scenario of SCENARIOS) {
  assert.ok(scenario.steps.length >= 3, `${scenario.scenarioId} requires a meaningful lifecycle`);
  assert.equal(scenario.steps.at(-1).terminal, true, `${scenario.scenarioId} terminal step must be reachable`);
  assert.ok(scenario.expectedTerminalState, `${scenario.scenarioId} requires an expected terminal state`);
  for (const [index, step] of scenario.steps.entries()) {
    assert.equal(step.sequence, index + 1, `${scenario.scenarioId} step sequence must be contiguous`);
    assert.equal(step.event.scenarioId, scenario.scenarioId, 'audit event scenario identity mismatch');
    assert.equal(step.event.logicalTime, step.logicalTime, 'audit event logical time mismatch');
    assert.ok(step.event.eventId && step.event.workloadId && step.event.decision, 'audit event identity is incomplete');
    assert.ok(step.provenance?.sourceType && step.event.provenance?.sourceType, 'step and event provenance required');
  }
}

const controller = new ScenarioController(SCENARIOS);
for (const scenarioId of REQUIRED_SCENARIO_IDS) {
  controller.select(scenarioId);
  const initial = controller.getState();
  controller.start();
  while (controller.canNext()) controller.next();
  const terminal = controller.getState();
  assert.equal(terminal.currentStep.terminal, true, `${scenarioId} did not reach terminal state`);
  assert.equal(terminal.status, terminal.scenario.expectedTerminalState, `${scenarioId} terminal status mismatch`);
  controller.reset();
  assert.deepEqual(controller.getState(), initial, `${scenarioId} reset is not deterministic`);
}

const quality = SCENARIOS.find((item) => item.scenarioId === 'quality-slo-conflict');
assert.ok(['COUNTEROFFER', 'REJECT', 'DEFER'].includes(quality.expectedTerminalState));
assert.ok(quality.safetyDecisions.includes('QUALITY_DEGRADATION_REJECTED'));
assert.equal(quality.requestedQualityFloor, quality.preservedQualityFloor);

const migration = SCENARIOS.find((item) => item.scenarioId === 'live-migration');
assert.equal(migration.authoritativeExecutorCount, 1);
assert.ok(migration.rollbackPath?.length >= 2);

const healing = SCENARIOS.find((item) => item.scenarioId === 'self-healing');
assert.ok(healing.alternateVerificationFailurePath?.includes('ESCALATE'));

const adversarial = SCENARIOS.find((item) => item.scenarioId === 'adversarial-counterfactual');
assert.equal(adversarial.executionAuthorized, false);
assert.equal(adversarial.calibrationState, 'UNCALIBRATED');

const federation = SCENARIOS.find((item) => item.scenarioId === 'federated-privacy');
assert.ok(federation.rejectedCandidates.length > 0);
assert.ok(federation.selectedCandidate || ['DEFER', 'REJECT'].includes(federation.expectedTerminalState));

const scenarioProvider = new ScenarioControlCenterProvider(new DemoControlCenterProvider(), controller);
controller.select('live-migration');
controller.start();
controller.next();
const projected = await scenarioProvider.getSnapshot();
assert.equal(projected.scenario.scenarioId, 'live-migration');
assert.equal(projected.scenario.currentStep.sequence, 2);
assert.equal(projected.migration.authority.authoritativeCount, 1);
assert.equal(projected.evidence[0].scenarioId, 'live-migration');
assert.equal(projected.overview.activeScenario.scenarioId, 'live-migration');

console.log('PASS: six deterministic scenarios validated');
console.log('PASS: transitions, terminal states, reset, provenance, and audit trails validated');
console.log('PASS: quality, migration, simulation, and federation safety boundaries validated');
console.log('PASS: cross-view scenario projection validated');
