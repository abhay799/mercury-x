import { validateScenarioCatalog } from './contracts.js';

export class ScenarioController {
  #scenarios;
  #selectedId;
  #stepIndex = 0;
  #started = false;

  constructor(scenarios) {
    validateScenarioCatalog(scenarios);
    this.#scenarios = scenarios;
    this.#selectedId = scenarios[0].scenarioId;
  }

  list() { return this.#scenarios; }

  select(scenarioId) {
    if (!this.#scenarios.some((scenario) => scenario.scenarioId === scenarioId)) throw new Error(`unknown scenario: ${scenarioId}`);
    this.#selectedId = scenarioId;
    this.#stepIndex = 0;
    this.#started = false;
    return this.getState();
  }

  start() {
    this.#started = true;
    return this.getState();
  }

  reset() {
    this.#stepIndex = 0;
    this.#started = false;
    return this.getState();
  }

  previous() {
    if (this.#stepIndex > 0) this.#stepIndex -= 1;
    return this.getState();
  }

  next() {
    const scenario = this.#selectedScenario();
    this.#started = true;
    if (this.#stepIndex < scenario.steps.length - 1) this.#stepIndex += 1;
    return this.getState();
  }

  canPrevious() { return this.#stepIndex > 0; }
  canNext() { return this.#stepIndex < this.#selectedScenario().steps.length - 1; }

  #selectedScenario() {
    return this.#scenarios.find((scenario) => scenario.scenarioId === this.#selectedId);
  }

  getState() {
    const scenario = this.#selectedScenario();
    const currentStep = scenario.steps[this.#stepIndex];
    return structuredClone({
      scenario,
      scenarioId: scenario.scenarioId,
      currentStep,
      stepIndex: this.#stepIndex,
      started: this.#started,
      canPrevious: this.canPrevious(),
      canNext: this.canNext(),
      status: currentStep.terminal ? scenario.expectedTerminalState : this.#started ? currentStep.status : 'READY',
      completedEvents: this.#started ? scenario.steps.slice(0, this.#stepIndex + 1).map((step) => step.event) : [],
    });
  }
}
