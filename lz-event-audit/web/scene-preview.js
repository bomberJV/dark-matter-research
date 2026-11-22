import { createSceneStore } from './scene-view.js';

const controls = document.querySelector('#scenario-controls');
const message = document.querySelector('#selection-status');

try {
  const store = createSceneStore(JSON.parse(document.querySelector('#scene-manifest').textContent));
  const panels = [...document.querySelectorAll('[data-scenario]')];
  const buttons = [...controls.querySelectorAll('button[data-select]')];
  if (panels.length !== store.scenarioIds.length || buttons.length !== store.scenarioIds.length) {
    throw new Error('Static view does not match recorded scenarios');
  }
  function select(id) {
    const view = store.select(id);
    for (const panel of panels) panel.hidden = panel.dataset.scenario !== id;
    for (const button of buttons) button.setAttribute('aria-pressed', String(button.dataset.select === id));
    message.textContent = `${view.scenario.label}. The reported event and both uncertainties are unchanged.`;
  }
  for (const button of buttons) button.addEventListener('click', () => select(button.dataset.select));
  select(store.scenarioIds[0]);
  controls.hidden = false;
} catch (error) {
  controls.hidden = true;
  for (const panel of document.querySelectorAll('[data-scenario]')) panel.hidden = false;
  message.textContent = 'Interactive selection is unavailable. All recorded scenarios remain below for comparison.';
  console.error('LZ scene preview:', error);
}
