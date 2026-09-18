import { DemoControlCenterProvider } from './data/demo-provider.js';
import { escapeHtml } from './components.js';
import { ScenarioController } from './scenarios/controller.js';
import { SCENARIOS } from './scenarios/definitions.js';
import { ScenarioControlCenterProvider } from './scenarios/scenario-provider.js';
import { renderView, VIEW_DEFINITIONS } from './views.js';

const scenarioController = new ScenarioController(SCENARIOS);
const provider = new ScenarioControlCenterProvider(new DemoControlCenterProvider(), scenarioController);
const state = { snapshot: null, selectedWorkload: null, route: 'overview', scenario: scenarioController.getState(), error: null };

const main = document.querySelector('#main-content');
const nav = document.querySelector('#primary-nav');
const routeLabel = document.querySelector('#route-label');
const sidebar = document.querySelector('#sidebar');
const menuButton = document.querySelector('#menu-button');
const scrim = document.querySelector('#scrim');

function routeFromHash() {
  const route = window.location.hash.replace(/^#\/?/, '').split('/')[0];
  return VIEW_DEFINITIONS.some(([id]) => id === route) ? route : 'overview';
}

function buildNavigation() {
  nav.innerHTML = VIEW_DEFINITIONS.map(([id, label, icon], index) => `
    ${[0, 3, 7, 12].includes(index) && index !== 0 ? '<div class="nav-divider" aria-hidden="true"></div>' : ''}
    <a class="nav-item" href="#/${id}" data-route-link="${id}">
      <span class="nav-item__icon" aria-hidden="true">${icon}</span>
      <span>${escapeHtml(label)}</span>
    </a>`).join('');
}

function updateNavigation() {
  const definition = VIEW_DEFINITIONS.find(([id]) => id === state.route);
  routeLabel.textContent = definition?.[1] ?? 'Mission Control';
  document.querySelectorAll('[data-route-link]').forEach((link) => {
    const active = link.dataset.routeLink === state.route;
    link.classList.toggle('is-active', active);
    if (active) link.setAttribute('aria-current', 'page');
    else link.removeAttribute('aria-current');
  });
}

function renderError(error) {
  main.innerHTML = `<div class="fatal-state" role="alert"><span aria-hidden="true">!</span><h1>Control snapshot unavailable</h1><p>${escapeHtml(error?.message ?? 'Unknown provider error')}</p><button class="primary-button" id="retry-button">Retry provider</button></div>`;
  document.querySelector('#retry-button')?.addEventListener('click', loadSnapshot);
}

function render() {
  updateNavigation();
  if (state.error) return renderError(state.error);
  if (!state.snapshot) return;
  main.innerHTML = `<div class="view-enter">${renderView(state.route, state.snapshot, state)}</div>`;
  main.focus({ preventScroll: true });
  window.scrollTo({ top: 0, behavior: 'instant' });
}

function closeMenu() {
  sidebar.classList.remove('is-open');
  menuButton.setAttribute('aria-expanded', 'false');
  scrim.hidden = true;
}

function navigate(route) {
  if (!VIEW_DEFINITIONS.some(([id]) => id === route)) return;
  window.location.hash = `/${route}`;
}

async function loadSnapshot() {
  state.error = null;
  main.innerHTML = '<div class="loading-state" role="status"><span class="loader" aria-hidden="true"></span><strong>Loading control-plane snapshot</strong><p>Validating provenance and evidence boundaries…</p></div>';
  try {
    state.snapshot = await provider.getSnapshot();
    state.scenario = scenarioController.getState();
    state.selectedWorkload ??= state.snapshot.workloads[0]?.id ?? null;
    render();
  } catch (error) {
    state.error = error;
    render();
  }
}

async function updateScenario(action, value) {
  if (action === 'select') scenarioController.select(value);
  else if (action === 'start') scenarioController.start();
  else if (action === 'reset') scenarioController.reset();
  else if (action === 'previous') scenarioController.previous();
  else if (action === 'next') scenarioController.next();
  state.scenario = scenarioController.getState();
  state.selectedWorkload = state.scenario.scenario.workloadId;
  state.snapshot = await provider.getSnapshot();
  render();
}

window.addEventListener('hashchange', () => {
  state.route = routeFromHash();
  closeMenu();
  render();
});

document.addEventListener('click', async (event) => {
  const scenarioSelect = event.target.closest('[data-scenario-id]');
  if (scenarioSelect) await updateScenario('select', scenarioSelect.dataset.scenarioId);
  const scenarioAction = event.target.closest('[data-scenario-action]');
  if (scenarioAction && !scenarioAction.disabled) await updateScenario(scenarioAction.dataset.scenarioAction);
  const routeButton = event.target.closest('[data-route]');
  if (routeButton) navigate(routeButton.dataset.route);
  const workloadButton = event.target.closest('[data-select-workload]');
  if (workloadButton) {
    state.selectedWorkload = workloadButton.dataset.selectWorkload;
    if (state.route !== 'workloads') navigate('workloads');
    else render();
  }
});

menuButton.addEventListener('click', () => {
  const open = sidebar.classList.toggle('is-open');
  menuButton.setAttribute('aria-expanded', String(open));
  scrim.hidden = !open;
});
scrim.addEventListener('click', closeMenu);
window.addEventListener('keydown', (event) => { if (event.key === 'Escape') closeMenu(); });

buildNavigation();
state.route = routeFromHash();
if (!window.location.hash) history.replaceState(null, '', '#/overview');
loadSnapshot();
