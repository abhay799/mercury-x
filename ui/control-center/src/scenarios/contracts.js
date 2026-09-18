import { SOURCE_TYPES } from '../types.js';

export const SCENARIO_SCHEMA = 'mercury.control-center.scenario/v1';
export const SCENARIO_SAFETY_STATES = Object.freeze(['ACCEPT', 'REJECT', 'COUNTEROFFER', 'DEFER', 'UNKNOWN', 'ESCALATE']);
export const SCENARIO_STATUS = Object.freeze(['READY', 'RUNNING', ...SCENARIO_SAFETY_STATES]);

const nonblank = (value, field) => {
  if (typeof value !== 'string' || !value.trim()) throw new Error(`${field} must be nonblank`);
};

function validateProvenance(value, field) {
  if (!value || typeof value !== 'object') throw new Error(`${field} provenance is required`);
  if (!SOURCE_TYPES.includes(value.sourceType) || value.sourceType === 'LIVE') throw new Error(`${field} uses invalid demo source type`);
  nonblank(value.generatedAt, `${field}.generatedAt`);
  nonblank(value.evidenceState, `${field}.evidenceState`);
  nonblank(value.calibrationState, `${field}.calibrationState`);
  if (!Array.isArray(value.sourceIds) || value.sourceIds.length === 0 || value.sourceIds.some((id) => !String(id).trim())) {
    throw new Error(`${field}.sourceIds must be nonempty`);
  }
}

export function validateScenario(scenario) {
  if (!scenario || scenario.schema !== SCENARIO_SCHEMA) throw new Error('unsupported scenario schema');
  for (const field of ['scenarioId', 'name', 'description', 'status', 'expectedTerminalState', 'workloadId']) nonblank(scenario[field], field);
  if (!SCENARIO_STATUS.includes(scenario.status)) throw new Error(`${scenario.scenarioId} has unsupported status`);
  if (!SCENARIO_SAFETY_STATES.includes(scenario.expectedTerminalState)) throw new Error(`${scenario.scenarioId} has unsupported terminal state`);
  validateProvenance(scenario.provenance, scenario.scenarioId);
  if (!Array.isArray(scenario.steps) || scenario.steps.length < 3) throw new Error(`${scenario.scenarioId} requires at least three steps`);
  scenario.steps.forEach((step, index) => {
    if (step.sequence !== index + 1) throw new Error(`${scenario.scenarioId} has non-contiguous sequence`);
    for (const field of ['stepId', 'label', 'logicalTime', 'status', 'decision', 'evidence', 'authority', 'safetyResult', 'verificationResult', 'route']) nonblank(step[field], `${scenario.scenarioId}.${field}`);
    validateProvenance(step.provenance, `${scenario.scenarioId}.${step.stepId}`);
    if (!step.event || step.event.scenarioId !== scenario.scenarioId || step.event.logicalTime !== step.logicalTime) throw new Error(`${scenario.scenarioId} event lineage mismatch`);
    for (const field of ['eventId', 'workloadId', 'decision', 'evidence', 'authority', 'safetyResult', 'verificationResult']) nonblank(step.event[field], `${scenario.scenarioId}.event.${field}`);
    validateProvenance(step.event.provenance, `${scenario.scenarioId}.${step.event.eventId}`);
  });
  if (!scenario.steps.at(-1).terminal) throw new Error(`${scenario.scenarioId} lacks reachable terminal step`);
  if (scenario.steps.at(-1).status !== scenario.expectedTerminalState) throw new Error(`${scenario.scenarioId} terminal status mismatch`);
  return scenario;
}

export function validateScenarioCatalog(scenarios) {
  if (!Array.isArray(scenarios) || scenarios.length === 0) throw new Error('scenario catalog is empty');
  const ids = scenarios.map((scenario) => scenario.scenarioId);
  if (new Set(ids).size !== ids.length) throw new Error('duplicate scenario identity');
  scenarios.forEach(validateScenario);
  return scenarios;
}

export function deepFreeze(value) {
  if (value && typeof value === 'object' && !Object.isFrozen(value)) {
    Object.freeze(value);
    Object.values(value).forEach(deepFreeze);
  }
  return value;
}
