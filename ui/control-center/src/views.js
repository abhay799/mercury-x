import {
  callout, chip, definitionList, emptyState, escapeHtml, metricCard, pageHeader,
  panel, progress, provenanceBadge, provenanceDetail, table,
} from './components.js';

const arrowFlow = (items, active = '') => `<div class="flow-strip">${items.map((item, index) => `
  <div class="flow-step ${item === active ? 'flow-step--active' : ''}"><span>${index + 1}</span>${escapeHtml(item)}</div>
  ${index < items.length - 1 ? '<span class="flow-arrow" aria-hidden="true">→</span>' : ''}`).join('')}</div>`;

const stageTimeline = (stages) => `<ol class="timeline">${stages.map(([name, state]) => `
  <li class="timeline__item timeline__item--${state.toLowerCase()}"><span class="timeline__rail" aria-hidden="true"></span><div><strong>${escapeHtml(name)}</strong>${chip(state)}</div></li>`).join('')}</ol>`;

const sourceLegend = () => `<div class="source-legend" aria-label="Data provenance legend">
  ${['STATIC DEMO', 'SYNTHETIC', 'SIMULATED', 'UNKNOWN'].map((item) => chip(item, item)).join('')}
  <span>Every displayed artifact declares its source class.</span>
</div>`;

const scenarioBanner = (data) => data.scenario ? `<aside class="scenario-banner">
  <div><span class="scenario-banner__pulse" aria-hidden="true"></span><p>ACTIVE DEMONSTRATION SCENARIO</p><strong>${escapeHtml(data.scenario.scenario.name)}</strong><code>${escapeHtml(data.scenario.scenarioId)}</code></div>
  <div><span>Current stage</span><strong>${escapeHtml(data.scenario.currentStep.label)}</strong><small>${escapeHtml(data.scenario.currentStep.logicalTime)}</small></div>
  <div>${chip(data.scenario.status)}${provenanceBadge(data.scenario.currentStep.provenance)}<button class="text-button" data-route="scenarios">Open player →</button></div>
</aside>` : '';

function overview(data) {
  const workloadRows = data.workloads.map((workload) => [
    `<button class="link-button" data-route="workloads" data-select-workload="${escapeHtml(workload.id)}">${escapeHtml(workload.id)}</button><small>${escapeHtml(workload.name)}</small>`,
    chip(workload.state), escapeHtml(workload.slo), escapeHtml(workload.placement), provenanceBadge(workload.provenance),
  ]);
  const decisionRows = data.evidence.slice(0, 3).map((event) => [
    `<code>${escapeHtml(event.id)}</code>`, escapeHtml(event.action), chip(event.outcome), provenanceBadge(event.provenance),
  ]);
  return `
    ${pageHeader('MISSION CONTROL', 'MERCURY X Control Center', 'A provenance-first view of the logical AI compute control plane.', data.system.provenance)}
    ${scenarioBanner(data)}
    ${sourceLegend()}
    ${callout('Demonstration boundary', data.notice, 'warning')}
    <div class="metric-grid">${data.overview.metrics.map(metricCard).join('')}</div>
    <div class="layout-grid layout-grid--wide">
      ${panel('Workload control state', table(['Workload', 'State', 'SLO', 'Placement', 'Source'], workloadRows, { compact: true }), { eyebrow: 'ACTIVE / SIMULATED WORKLOADS' })}
      ${panel('Invariant watch', data.overview.signals.map((signal) => `<div class="signal-row"><div><span>${escapeHtml(signal.label)}</span><strong>${escapeHtml(signal.value)}</strong></div><div>${chip(signal.state)}${provenanceBadge(signal.provenance)}</div></div>`).join(''), { eyebrow: 'SAFETY AND GOVERNANCE' })}
    </div>
    <div class="layout-grid">
      ${panel('Current control path', arrowFlow(['Sense', 'Understand', 'Plan', 'Place', 'Negotiate', 'Verify'], 'Negotiate'), { eyebrow: 'SYSTEM LIFECYCLE' })}
      ${panel('Recent decisions', table(['Decision', 'Action', 'Outcome', 'Source'], decisionRows, { compact: true }), { eyebrow: 'TRACEABLE EVENTS', action: '<button class="text-button" data-route="evidence">Open audit →</button>' })}
    </div>`;
}

function workloads(data, state) {
  const selected = data.workloads.find((item) => item.id === state.selectedWorkload) ?? data.workloads[0];
  const stages = ['Request', 'Classification', 'Execution graph', 'Model / capability', 'Precision', 'Placement', 'Reasoning budget', 'SLO', 'Negotiation', 'Execution state'];
  return `
    ${pageHeader('WORKLOAD INTELLIGENCE', 'Workloads', 'Inspect the evidence-backed path from canonical request to execution state.', selected.provenance)}
    ${scenarioBanner(data)}
    <div class="workload-tabs" role="tablist" aria-label="Demo workloads">${data.workloads.map((item) => `<button role="tab" aria-selected="${item.id === selected.id}" class="workload-tab ${item.id === selected.id ? 'is-active' : ''}" data-select-workload="${escapeHtml(item.id)}">${escapeHtml(item.id)}<span>${escapeHtml(item.name)}</span></button>`).join('')}</div>
    <div class="layout-grid layout-grid--detail">
      ${panel(selected.name, `${definitionList([
        ['Workload ID', selected.id], ['Modality', selected.modality], ['State', selected.state], ['Quality floor', selected.qualityFloor],
        ['Model', selected.model], ['Precision', selected.precision], ['Placement', selected.placement], ['Reasoning budget', selected.reasoningBudget],
        ['Intelligence SLO', selected.slo], ['Negotiation', selected.negotiation],
      ])}`, { eyebrow: 'CONTROL ARTIFACT', action: chip(selected.state) })}
      ${provenanceDetail(selected.provenance)}
    </div>
    ${panel('Workload decision path', arrowFlow(stages, selected.state === 'UNKNOWN' ? 'Classification' : selected.state === 'DEFER' ? 'Placement' : 'Execution state'), { eyebrow: 'PHASE HANDOFFS' })}
    ${selected.state === 'UNKNOWN' ? callout('Fail-closed state', 'Required context evidence is incomplete. MERCURY does not infer approval or placement.', 'danger') : ''}`;
}

function executionGraph(data) {
  return `
    ${pageHeader('LOGICAL DAG', 'Execution Graph', 'A deterministic logical graph; placement labels are control artifacts, not proof of distributed execution.', data.graph.provenance)}
    ${panel(data.graph.graphId, `<div class="dag">${data.graph.nodes.map((node, index) => `
      <article class="dag-node"><div class="dag-node__index">${index + 1}</div><p>${escapeHtml(node.type)}</p><h3>${escapeHtml(node.label)}</h3>${chip(node.state)}
      <dl><div><dt>Capability / model</dt><dd>${escapeHtml(node.model)}</dd></div><div><dt>Placement</dt><dd>${escapeHtml(node.placement)}</dd></div><div><dt>Context</dt><dd>${escapeHtml(node.context)}</dd></div></dl></article>
      ${index < data.graph.nodes.length - 1 ? '<div class="dag-edge" aria-label="dependency">→</div>' : ''}`).join('')}</div>`, { eyebrow: 'INPUT → RETRIEVAL → REASONING → VALIDATION → OUTPUT', action: provenanceBadge(data.graph.provenance) })}
    <div class="layout-grid">
      ${panel('Dependency contract', table(['Source', 'Target', 'Relationship'], data.graph.edges.map(([from, to]) => [`<code>${from}</code>`, `<code>${to}</code>`, 'DATA / CONTROL'])), { eyebrow: 'VALIDATED EDGES' })}
      ${panel('Graph safeguards', ['Acyclic topology', 'No dangling edges', 'Capability coverage', 'Context lineage', 'Output verification'].map((item) => `<div class="check-row"><span aria-hidden="true">✓</span>${escapeHtml(item)}${chip('VERIFIED')}</div>`).join(''), { eyebrow: 'READINESS' })}
    </div>`;
}

function modelPrecision(data) {
  const rows = data.models.map((model) => [
    escapeHtml(model.stage), `<strong>${escapeHtml(model.identity)}</strong><small>${escapeHtml(model.revision)}</small>`, escapeHtml(model.capability),
    chip(model.precision), escapeHtml(model.adaptation), escapeHtml(model.quality), chip(model.calibration), provenanceBadge(model.provenance),
  ]);
  return `
    ${pageHeader('MODEL ADAPTATION', 'Model & Precision Intelligence', 'Exact identity, revision, capability, precision, and adaptation evidence remain visible.', data.models[0].provenance)}
    ${callout('Calibration honesty', 'These demonstration records are synthetic and explicitly UNCALIBRATED. No empirical quality number is claimed.', 'warning')}
    ${panel('Composition profile', table(['Stage', 'Model / revision', 'Capabilities', 'Precision', 'Adaptation', 'Quality constraint', 'Calibration', 'Source'], rows), { eyebrow: 'PRIMARY → VERIFIER' })}
    <div class="layout-grid">
      ${panel('Selection boundary', arrowFlow(['Capability match', 'Composition pattern', 'Precision compatibility', 'Registered morph', 'Validation'], 'Validation'), { eyebrow: 'CONTROL-PLANE PIPELINE' })}
      ${panel('Non-authorities', ['No hardware matching in model contracts', 'No hidden ranking score', 'No cross-family substitution', 'No live self-modification'].map((item) => `<div class="guard-row"><span aria-hidden="true">⊘</span>${escapeHtml(item)}</div>`).join(''), { eyebrow: 'BOUNDARY' })}
    </div>`;
}

function memoryContext(data) {
  return `
    ${pageHeader('MEMORY FABRIC', 'Memory & Context', 'Session isolation, governed promotion, and semantic cache compatibility.', data.memory.session[0].provenance)}
    <div class="layout-grid layout-grid--three">
      ${panel('Session memory', table(['Scope', 'Records', 'Lifecycle', 'Key'], data.memory.session.map((item) => [chip(item.scope), String(item.records), chip(item.lifecycle), escapeHtml(item.key)]), { compact: true }), { eyebrow: 'TURN / TASK / SESSION' })}
      ${panel('Global context', data.memory.global.map((item) => `<article class="record-card"><div>${chip(item.state)}${provenanceBadge(item.provenance)}</div><h3>${escapeHtml(item.namespace)}</h3><p>${item.records} versioned records</p><strong>${escapeHtml(item.authorization)}</strong></article>`).join(''), { eyebrow: 'AUTHORIZED NAMESPACES' })}
      ${panel('Semantic KV state', definitionList([['Identity', data.memory.cache.identity], ['Reuse state', data.memory.cache.status], ['Compatibility', data.memory.cache.compatibility]]), { eyebrow: 'EXACT REUSE BOUNDARY', action: provenanceBadge(data.memory.cache.provenance) })}
    </div>
    ${callout('Isolation invariant', 'No implicit global, user-profile, cross-session, or cross-namespace access is represented.', 'info')}`;
}

function computeFabric(data) {
  const lineMarkup = data.compute.links.map((link, index) => `<line x1="${[17, 50, 82, 50][index]}%" y1="${[52, 22, 54, 82][index]}%" x2="${[50, 82, 50, 17][index]}%" y2="${[22, 54, 82, 52][index]}%" class="topology-link topology-link--${link.state.toLowerCase()}" />`).join('');
  return `
    ${pageHeader('COMPUTE FABRIC', 'Hardware, Topology & Placement', 'Synthetic resource personalities and generation-aware placement evidence.', data.compute.provenance)}
    ${scenarioBanner(data)}
    <div class="layout-grid layout-grid--fabric">
      ${panel('Topology generation 42', `<div class="topology-canvas"><svg aria-hidden="true">${lineMarkup}</svg>${data.compute.nodes.map((node) => `<article class="topology-node topology-node--${node.health.toLowerCase()}" style="left:${node.x}%;top:${node.y}%"><span class="topology-node__pulse"></span><h3>${escapeHtml(node.id)}</h3><p>${escapeHtml(node.personality)}</p><div>${chip(node.health)} ${provenanceBadge(node.provenance)}</div></article>`).join('')}</div>`, { eyebrow: 'SYNTHETIC LOGICAL TOPOLOGY', action: chip('GENERATION 42') })}
      ${panel('Resource state', data.compute.nodes.map((node) => `<div class="resource-row"><div><strong>${escapeHtml(node.id)}</strong><span>${escapeHtml(node.personality)}</span></div><div>${progress(parseInt(node.utilization, 10), 100, 'Utilization')}<small>${node.placements} placement artifact(s)</small></div></div>`).join(''), { eyebrow: 'NOT LIVE TELEMETRY' })}
    </div>
    ${callout('Infrastructure boundary', 'Nodes, utilization, health, and paths are synthetic or simulated control-plane records—not connected hardware telemetry.', 'warning')}`;
}

function sloReasoning(data) {
  const reason = data.slo.reasoning;
  return `
    ${pageHeader('INTELLIGENCE CONTRACT', 'SLO, Reasoning & Negotiation', 'Protected quality floors and explicit resource reasoning drive fail-closed negotiation.', data.slo.provenance)}
    ${scenarioBanner(data)}
    ${data.slo.scenarioConflict ? callout('Scenario constraint conflict', `Requested quality ${data.slo.scenarioConflict.requestedQualityFloor} is preserved while only ${data.slo.scenarioConflict.availableResourceUnits} of ${data.slo.scenarioConflict.requestedResourceUnits} logical resource units are available. Current decision: ${data.slo.scenarioConflict.status}.`, 'danger') : ''}
    <div class="metric-grid metric-grid--compact">
      ${[
        { label: 'Quality floor', value: data.slo.qualityFloor, detail: 'Protected · cannot auto-degrade', provenance: data.slo.provenance },
        { label: 'Confidence floor', value: data.slo.confidenceFloor, detail: 'Typed intelligence requirement', provenance: data.slo.provenance },
        { label: 'Verification depth', value: data.slo.verificationDepth, detail: 'Hard minimum', provenance: data.slo.provenance },
        { label: 'Negotiation', value: data.slo.negotiation, detail: data.slo.resourceRequest, provenance: data.slo.provenance },
      ].map(metricCard).join('')}
    </div>
    <div class="layout-grid">
      ${panel('Reasoning budget', `<div class="budget-bars">${Object.entries(reason).filter(([key]) => key !== 'unit').map(([key, value]) => progress(value, 31, key.replace(/\b\w/g, (c) => c.toUpperCase()))).join('')}</div><p class="caption">Units are logical budget allocations, not measured GPU time.</p>`, { eyebrow: 'RB-410 · 31 LOGICAL UNITS' })}
      ${panel('Protected constraints', `<div class="shield-grid">${data.slo.protected.map((item) => `<div><span aria-hidden="true">◆</span>${escapeHtml(item)}</div>`).join('')}</div>`, { eyebrow: 'NO SILENT QUALITY DEGRADATION', action: chip('ENFORCED') })}
    </div>
    ${panel('Negotiation boundary', arrowFlow(['Requirements', 'Feasibility', 'Offer', 'Approval if changed', 'Atomic agreement'], 'Atomic agreement'), { eyebrow: 'ACCEPT / REJECT / COUNTEROFFER / UNKNOWN' })}`;
}

function migrationRecovery(data) {
  return `
    ${pageHeader('RESILIENCE CONTROL', 'Migration & Recovery', 'Verified cutover and bounded healing without claiming physical GPU or VM live-memory transfer.', data.migration.provenance)}
    ${scenarioBanner(data)}
    <div class="layout-grid layout-grid--wide">
      ${panel('Migration lifecycle', stageTimeline(data.migration.stages), { eyebrow: `${data.migration.migrationId} · GENERATION ${data.migration.generation}`, action: chip(data.migration.state) })}
      ${panel('Authority and rollback', `${definitionList([['Fingerprint', data.migration.fingerprint], ['Source authority', data.migration.authority.source], ['Destination authority', data.migration.authority.destination], ['Authoritative executors', String(data.migration.authority.authoritativeCount)], ['Rollback', data.migration.rollback]])}<div class="authority-lock"><span aria-hidden="true">◈</span><strong>Exactly one authoritative executor</strong><p>Node A remains authoritative until verified atomic cutover.</p></div>`, { eyebrow: 'CUTOVER INVARIANT' })}
    </div>
    ${panel('Preserved control state', `<div class="tag-list tag-list--large">${data.migration.preserved.map((item) => `<span class="tag">${escapeHtml(item)}</span>`).join('')}</div>`, { eyebrow: 'CHECKPOINT / RESTORE EQUIVALENCE' })}
    <div class="layout-grid">
      ${panel('Self-healing lifecycle', stageTimeline(data.healing.steps), { eyebrow: data.healing.trigger, action: chip(data.healing.state) })}
      ${panel('Recovery decision', `${definitionList([['Decision', data.healing.decision], ['Verification', data.healing.verification]])}${callout('Recovery boundary', 'A safe action is not complete until post-recovery verification passes.', 'info')}`, { eyebrow: 'PHASE 22' })}
    </div>`;
}

function schedulerIntelligence(data) {
  return `
    ${pageHeader('CHALLENGE AND EVOLVE', 'Scheduler Intelligence', 'Adversarial challenge, advisory counterfactuals, and human-governed policy evolution.', data.scheduler.policy.provenance)}
    ${scenarioBanner(data)}
    <div class="layout-grid">
      ${panel('Adversarial challenges', data.scheduler.challenges.map((item) => `<article class="risk-card"><div>${chip(item.severity)}${provenanceBadge(item.provenance)}</div><h3>${escapeHtml(item.risk)}</h3><p><code>${escapeHtml(item.id)}</code></p>${chip(item.outcome)}</article>`).join(''), { eyebrow: 'PHASE 23' })}
      ${panel('Counterfactual alternatives', data.scheduler.alternatives.map((item) => `<article class="alternative"><div><strong>${escapeHtml(item.scenario)}</strong><p>Uncertainty: ${escapeHtml(item.uncertainty)}</p></div><div>${chip(item.outcome)}${provenanceBadge(item.provenance)}</div></article>`).join(''), { eyebrow: 'PHASE 24 · ADVISORY' })}
    </div>
    ${panel('Controlled policy evolution', `${arrowFlow(data.scheduler.policy.path, data.scheduler.policy.stage)}${callout('Human promotion gate', 'The candidate cannot enter production without explicit human approval. Autonomous promotion is forbidden.', 'warning')}`, { eyebrow: `PHASE 25 · ${data.scheduler.policy.id}`, action: chip(data.scheduler.policy.promoted ? 'PROMOTED' : 'NOT PROMOTED') })}`;
}

function federationPrivacy(data) {
  const rows = data.federation.domains.map((domain) => [
    `<strong>${escapeHtml(domain.id)}</strong><small>${escapeHtml(domain.class)}</small>`, escapeHtml(domain.residency), chip(domain.authorization), chip(domain.state), provenanceBadge(domain.provenance),
  ]);
  return `
    ${pageHeader('DOMAIN-AWARE CONTROL', 'Federation & Privacy', 'Exact execution-domain identity combined with purpose, residency, and minimum-necessary access.', data.federation.privacy.provenance)}
    ${scenarioBanner(data)}
    <div class="layout-grid layout-grid--wide">
      ${panel('Federated execution domains', table(['Domain', 'Residency', 'Authorization', 'State', 'Source'], rows), { eyebrow: 'PHASE 26' })}
      ${panel('Privacy envelope', `${definitionList([['Classification', data.federation.privacy.classification], ['Purpose', data.federation.privacy.purpose], ['Residency', data.federation.privacy.residency], ['Access', data.federation.privacy.access], ['Logging', data.federation.privacy.logging]])}<div class="privacy-seal"><span aria-hidden="true">⬡</span><strong>FAIL CLOSED</strong><p>Insufficient evidence or authority cannot broaden access.</p></div>`, { eyebrow: 'PHASE 27', action: provenanceBadge(data.federation.privacy.provenance) })}
    </div>`;
}

function digitalTwin(data) {
  return `
    ${pageHeader('SIMULATED / ADVISORY', 'Datacenter Digital Twin', 'A bounded, explicitly uncalibrated scenario interface. Nothing here is live telemetry.', data.twin.provenance)}
    ${callout('Not a calibrated production twin', 'This view uses simulated scenario data and cannot authorize or execute infrastructure changes.', 'danger')}
    <div class="layout-grid layout-grid--detail">
      ${panel(data.twin.title, `${definitionList([['Scenario', data.twin.scenarioId], ['Calibration', data.twin.calibration], ['Status', data.twin.status]])}<h3 class="subheading">Scenario inputs</h3><ul class="plain-list">${data.twin.inputs.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ul>`, { eyebrow: 'HYPOTHETICAL ENVIRONMENT', action: chip(data.twin.status) })}
      ${provenanceDetail(data.twin.provenance)}
    </div>
    ${panel('Simulated alternatives', data.twin.alternatives.map((item, index) => `<article class="scenario-row"><span>${String(index + 1).padStart(2, '0')}</span><div><strong>${escapeHtml(item.action)}</strong><p>${escapeHtml(item.effect)}</p></div>${chip(item.confidence)}</article>`).join(''), { eyebrow: 'NO PRODUCTION SIDE EFFECTS' })}`;
}

function governance(data) {
  const rows = data.governance.decisions.map((decision) => [
    `<code>${escapeHtml(decision.id)}</code>`, escapeHtml(decision.objective), escapeHtml(decision.authority), chip(decision.state), chip(decision.outcome), provenanceBadge(decision.provenance),
  ]);
  return `
    ${pageHeader('SUPERVISORY BOUNDARY', 'Governance & Control Intelligence', 'Evidence and authority pass through safety gates before any execution authorization.', data.governance.decisions[0].provenance)}
    ${panel('Control decision pipeline', arrowFlow(data.governance.pipeline, 'Human escalation'), { eyebrow: 'PHASE 29' })}
    ${panel('Supervisory decisions', table(['Decision', 'Objective', 'Authority', 'State', 'Outcome', 'Source'], rows), { eyebrow: 'UNKNOWN / DEFER / ESCALATE ARE FIRST-CLASS' })}
    ${callout('Human control', 'Evidence can recommend or challenge. It cannot autonomously grant authority or promote production policy.', 'warning')}`;
}

function evidenceAudit(data) {
  const rows = data.evidence.map((event) => [
    `<code>${escapeHtml(event.id)}</code><small>${escapeHtml(event.timestamp)}</small>`, `<strong>${escapeHtml(event.workload)}</strong><small>${escapeHtml(event.source)}</small>`,
    chip(event.evidence), escapeHtml(event.policy), escapeHtml(event.authority), escapeHtml(event.action), chip(event.verification), chip(event.outcome), provenanceBadge(event.provenance),
  ]);
  return `
    ${pageHeader('TRACEABILITY', 'Evidence & Audit', 'Decision artifacts remain attributable to evidence, policy, authority, action, and verification.', data.evidence[0]?.provenance)}
    ${scenarioBanner(data)}
    ${data.evidence.length ? panel('Decision ledger', table(['Decision / time', 'Workload / source', 'Evidence', 'Policy', 'Authority', 'Action', 'Verification', 'Outcome', 'Provenance'], rows), { eyebrow: 'APPEND-ONLY DEMONSTRATION VIEW' }) : emptyState('No evidence records', 'Connect an authorized provider or load a demonstration snapshot.')}
    ${callout('Audit boundary', 'This view demonstrates traceable artifacts. It is not an external compliance attestation or production audit log.', 'info')}`;
}

function systemStatus(data) {
  return `
    ${pageHeader('SYSTEM / RESEARCH STATUS', 'Platform Boundary', 'The current repository scope, evidence categories, and unclaimed infrastructure integrations.', data.system.provenance)}
    <div class="layout-grid layout-grid--detail">
      ${panel('Repository state', definitionList([['Certified phase range', data.system.phaseRange], ['Regression evidence', data.system.regression], ['Interface mode', data.system.mode], ['Backend boundary', data.system.backend]]), { eyebrow: 'MERCURY PLATFORM' })}
      ${provenanceDetail(data.system.provenance)}
    </div>
    ${panel('Claim matrix', data.system.claims.map(([claim, status]) => `<div class="claim-row"><strong>${escapeHtml(claim)}</strong>${chip(status)}</div>`).join(''), { eyebrow: 'IMPLEMENTED · SIMULATED · NOT CLAIMED' })}
    ${callout('Research mode cannot weaken production guarantees', 'Quality, safety, privacy, authorization, verification, and human-control invariants remain binding in every platform mode.', 'warning')}`;
}

function scenarioPlayer(data, state) {
  const playback = state.scenario ?? data.scenario;
  if (!playback) return `${pageHeader('DEMONSTRATION SYSTEM', 'Scenario Player', 'No scenario provider is connected.')} ${emptyState('No scenarios available', 'Connect a scenario provider to begin.')}`;
  const scenario = playback.scenario;
  const step = playback.currentStep;
  const completed = playback.started ? scenario.steps.slice(0, playback.stepIndex + 1) : [];
  const scenarioTabs = (data.scenarioCatalog ?? []).map((item, index) => `<button class="scenario-card ${item.scenarioId === scenario.scenarioId ? 'is-active' : ''}" data-scenario-id="${escapeHtml(item.scenarioId)}" aria-pressed="${item.scenarioId === scenario.scenarioId}"><span>${String(index + 1).padStart(2, '0')}</span><div><strong>${escapeHtml(item.name)}</strong><small>${escapeHtml(item.expectedTerminalState)} · ${item.steps.length} stages</small></div>${provenanceBadge(item.provenance)}</button>`).join('');
  const eventRows = completed.map((event) => [
    `<code>${escapeHtml(event.event.eventId)}</code><small>${escapeHtml(event.logicalTime)}</small>`, escapeHtml(event.label), chip(event.status),
    escapeHtml(event.event.authority), escapeHtml(event.event.safetyResult), chip(event.event.verificationResult), provenanceBadge(event.event.provenance),
  ]);
  return `
    ${pageHeader('DETERMINISTIC DEMONSTRATION', 'Scenario Player', 'Step through reproducible control-plane decisions and inspect why each transition occurs.', scenario.provenance)}
    <div class="scenario-layout">
      <aside class="scenario-catalog" aria-label="Scenario selector"><p class="eyebrow">SCENARIO CATALOG</p>${scenarioTabs}</aside>
      <div class="scenario-stage">
        <section class="scenario-hero">
          <div><div class="scenario-hero__meta">${chip(playback.status)}${provenanceBadge(step.provenance)}<code>${escapeHtml(scenario.scenarioId)}</code></div><h2>${escapeHtml(scenario.name)}</h2><p>${escapeHtml(scenario.description)}</p></div>
          <div class="scenario-progress"><strong>${playback.stepIndex + 1}<span> / ${scenario.steps.length}</span></strong><p>Lifecycle stage</p></div>
        </section>
        <div class="scenario-controls" aria-label="Scenario playback controls">
          <button class="secondary-button" data-scenario-action="reset">↺ Reset</button>
          <button class="secondary-button" data-scenario-action="previous" ${playback.canPrevious ? '' : 'disabled'}>← Previous</button>
          <button class="primary-button" data-scenario-action="start" ${playback.started ? 'disabled' : ''}>${playback.started ? 'Started' : 'Start scenario'}</button>
          <button class="secondary-button" data-scenario-action="next" ${playback.canNext ? '' : 'disabled'}>Next step →</button>
        </div>
        ${panel('Lifecycle', `<div class="scenario-lifecycle">${scenario.steps.map((item, index) => `<div class="scenario-lifecycle__step ${index < playback.stepIndex ? 'is-complete' : index === playback.stepIndex ? 'is-current' : ''}"><span>${index + 1}</span><strong>${escapeHtml(item.label)}</strong><small>${escapeHtml(item.route)}</small></div>`).join('')}</div>`, { eyebrow: `${step.logicalTime} · EXPECTED ${scenario.expectedTerminalState}` })}
        <div class="layout-grid layout-grid--detail">
          ${panel(step.label, `${step.explanation ? `<p class="decision-explanation">${escapeHtml(step.explanation)}</p>` : ''}${definitionList([['Decision', step.decision], ['Evidence', step.evidence], ['Authority', step.authority], ['Safety result', step.safetyResult], ['Verification', step.verificationResult]])}`, { eyebrow: 'WHY THIS DECISION OCCURRED', action: chip(step.status) })}
          ${panel('Affected resources', `<div class="tag-list tag-list--large">${(step.affectedResources.length ? step.affectedResources : scenario.affectedResources).map((item) => `<span class="tag">${escapeHtml(item)}</span>`).join('')}</div><h3 class="subheading">Expected outcome</h3><div class="expected-outcome">${chip(scenario.expectedTerminalState)}<span>${escapeHtml(scenario.steps.at(-1).explanation)}</span></div>`, { eyebrow: 'IMPACT BOUNDARY' })}
        </div>
        <div class="layout-grid">
          ${panel('Safety invariants', scenario.safetyDecisions.map((item) => `<div class="check-row"><span aria-hidden="true">✓</span>${escapeHtml(item)}${chip('ENFORCED')}</div>`).join(''), { eyebrow: 'NO SILENT FALLTHROUGH' })}
          ${provenanceDetail(step.provenance)}
        </div>
        ${scenario.rollbackPath ? callout('Inspectable rollback path', scenario.rollbackPath.join(' → '), 'warning') : ''}
        ${scenario.alternateVerificationFailurePath ? callout('Verification failure branch', scenario.alternateVerificationFailurePath.join(' → '), 'danger') : ''}
        ${panel('Scenario audit trail', eventRows.length ? table(['Event / time', 'Stage', 'State', 'Authority', 'Safety', 'Verification', 'Source'], eventRows, { compact: true }) : emptyState('Scenario not started', 'Start the scenario to emit its first deterministic audit event.'), { eyebrow: 'DETERMINISTIC EVENTS' })}
      </div>
    </div>`;
}

export const VIEW_DEFINITIONS = Object.freeze([
  ['overview', 'Mission Control', '⌁'], ['scenarios', 'Scenario Player', '▷'], ['workloads', 'Workloads', '◫'], ['graph', 'Execution Graph', '⌘'],
  ['models', 'Model & Precision', '◇'], ['memory', 'Memory & Context', '◧'], ['compute', 'Compute Fabric', '⬡'],
  ['slo', 'SLO & Reasoning', '◎'], ['migration', 'Migration & Recovery', '↬'], ['scheduler', 'Scheduler Intelligence', '△'],
  ['federation', 'Federation & Privacy', '⊙'], ['twin', 'Digital Twin', '◌'], ['governance', 'Governance', '◆'],
  ['evidence', 'Evidence & Audit', '≡'], ['system', 'System Status', '◉'],
]);

const renderers = { overview, scenarios: scenarioPlayer, workloads, graph: executionGraph, models: modelPrecision, memory: memoryContext, compute: computeFabric, slo: sloReasoning, migration: migrationRecovery, scheduler: schedulerIntelligence, federation: federationPrivacy, twin: digitalTwin, governance, evidence: evidenceAudit, system: systemStatus };

export function renderView(viewId, data, state) {
  return (renderers[viewId] ?? renderers.overview)(data, state);
}
