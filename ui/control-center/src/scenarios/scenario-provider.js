const clone = (value) => structuredClone(value);

function merge(target, patch) {
  if (!patch || typeof patch !== 'object' || Array.isArray(patch)) return clone(patch);
  const output = { ...(target ?? {}) };
  for (const [key, value] of Object.entries(patch)) {
    output[key] = value && typeof value === 'object' && !Array.isArray(value) ? merge(output[key], value) : clone(value);
  }
  return output;
}

function auditRecord(playback) {
  const event = playback.currentStep.event;
  return {
    id: event.eventId,
    scenarioId: event.scenarioId,
    workload: event.workloadId,
    timestamp: event.logicalTime,
    source: event.evidence,
    evidence: event.provenance.evidenceState,
    policy: event.safetyResult,
    authority: event.authority,
    action: event.decision,
    verification: event.verificationResult,
    outcome: playback.currentStep.status,
    safetyResult: event.safetyResult,
    provenance: event.provenance,
  };
}

export function projectScenarioSnapshot(baseSnapshot, playback) {
  const snapshot = clone(baseSnapshot);
  const { scenario, currentStep } = playback;
  snapshot.scenario = playback;
  snapshot.scenarioCatalog = thisCatalog(playback, baseSnapshot);
  snapshot.overview.activeScenario = {
    scenarioId: scenario.scenarioId, name: scenario.name, step: currentStep.label,
    logicalTime: currentStep.logicalTime, status: playback.status,
    provenance: currentStep.provenance,
  };
  if (playback.started) {
    snapshot.evidence = [auditRecord(playback), ...snapshot.evidence.filter((item) => item.id !== currentStep.event.eventId)];
  }

  const existing = snapshot.workloads.find((item) => item.id === scenario.workloadId);
  const scenarioWorkload = existing ?? {
    id: scenario.workloadId, name: scenario.name, modality: 'CONTROL-PLANE SCENARIO', qualityFloor: scenario.requestedQualityFloor ?? '0.92',
    placement: scenario.affectedResources.join(' / '), slo: 'scenario-slo', model: 'scenario exact identity', precision: 'scenario profile',
    reasoningBudget: 'scenario budget', negotiation: 'PENDING', provenance: scenario.provenance,
  };
  Object.assign(scenarioWorkload, {
    state: currentStep.projection.workloadState ?? currentStep.status,
    negotiation: currentStep.projection.negotiation ?? scenarioWorkload.negotiation,
    provenance: currentStep.provenance,
  });
  if (!existing) snapshot.workloads.unshift(scenarioWorkload);

  snapshot.compute.scenarioState = {
    scenarioId: scenario.scenarioId, step: currentStep.label,
    affectedResources: currentStep.affectedResources.length ? currentStep.affectedResources : scenario.affectedResources,
    provenance: currentStep.provenance,
  };

  if (scenario.scenarioId === 'quality-slo-conflict') {
    snapshot.slo.scenarioConflict = {
      requestedQualityFloor: scenario.requestedQualityFloor,
      preservedQualityFloor: scenario.preservedQualityFloor,
      requestedResourceUnits: scenario.requestedResourceUnits,
      availableResourceUnits: scenario.availableResourceUnits,
      decision: currentStep.decision,
      status: currentStep.status,
      provenance: currentStep.provenance,
    };
    snapshot.slo.negotiation = currentStep.projection.negotiation ?? currentStep.status;
  }

  if (scenario.scenarioId === 'live-migration') {
    const active = playback.stepIndex;
    snapshot.migration = merge(snapshot.migration, {
      migrationId: scenario.scenarioId,
      generation: 21,
      fingerprint: 'sha256:scenario-live-migration-v1',
      state: currentStep.label.toUpperCase(),
      authority: {
        source: currentStep.projection.migrationAuthority === 'node-b' ? 'RETIRED' : 'AUTHORITATIVE',
        destination: currentStep.projection.migrationAuthority === 'node-b' ? 'AUTHORITATIVE' : 'NOT AUTHORITATIVE',
        authoritativeCount: scenario.authoritativeExecutorCount,
      },
      stages: scenario.steps.map((step, index) => [step.label, index < active ? 'COMPLETE' : index === active ? 'ACTIVE' : 'PENDING']),
      rollback: scenario.rollbackPath.join(' → '), provenance: currentStep.provenance,
    });
  }

  if (scenario.scenarioId === 'self-healing') {
    const active = playback.stepIndex;
    snapshot.healing = merge(snapshot.healing, {
      state: currentStep.label.toUpperCase(),
      steps: scenario.steps.map((step, index) => [step.label, index < active ? 'COMPLETE' : index === active ? 'ACTIVE' : 'PENDING']),
      decision: currentStep.decision,
      verification: currentStep.verificationResult,
      failurePath: scenario.alternateVerificationFailurePath,
      provenance: currentStep.provenance,
    });
  }

  if (scenario.scenarioId === 'adversarial-counterfactual') {
    snapshot.scheduler.activeScenario = {
      step: currentStep.label, decision: currentStep.decision, executionAuthorized: false,
      calibrationState: scenario.calibrationState, provenance: currentStep.provenance,
    };
  }

  if (scenario.scenarioId === 'federated-privacy') {
    snapshot.federation.activeScenario = {
      step: currentStep.label, selectedCandidate: currentStep.terminal ? scenario.selectedCandidate : null,
      rejectedCandidates: scenario.rejectedCandidates, provenance: currentStep.provenance,
    };
  }
  return snapshot;
}

function thisCatalog(playback) {
  return playback.scenarioCatalog ?? [];
}

export class ScenarioControlCenterProvider {
  constructor(baseProvider, controller) {
    this.baseProvider = baseProvider;
    this.controller = controller;
  }

  listScenarios() { return this.controller.list(); }
  getScenarioState() { return this.controller.getState(); }

  async getSnapshot() {
    const playback = this.controller.getState();
    playback.scenarioCatalog = this.controller.list();
    return projectScenarioSnapshot(await this.baseProvider.getSnapshot(), playback);
  }
}
