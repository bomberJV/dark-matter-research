import { createSceneStore } from './scene-view.js';

// Presentation state only. No interpolation, fitting, rate integration or new physics.
export function createExperience(manifest) {
  const store = createSceneStore(manifest);
  if (store.scenarioIds.join('|') !== 'base|vesc600') throw new TypeError('Expected the two reviewed snapshots');
  let current = 'base';
  return Object.freeze({
    get current() { return current; },
    get observation() { return store.manifest.observation; },
    select(id) {
      const view = store.select(id); // Reject unsupported values before changing state.
      current = id;
      return view;
    },
    record() { return store.manifest; },
  });
}

export function mountExperience(doc) {
  const embedded = doc.getElementById('scene-manifest');
  if (!embedded) return null;
  let experience;
  try { experience = createExperience(JSON.parse(embedded.textContent)); }
  catch { return null; } // The complete static comparison stays readable on failure.
  const panels = [...doc.querySelectorAll('[data-recorded-scenario]')];
  const choices = [...doc.querySelectorAll('[data-scenario-choice]')];
  if (panels.length !== 2 || choices.length !== 2
      || panels.map((p) => p.dataset.recordedScenario).join('|') !== 'base|vesc600'
      || choices.map((p) => p.dataset.scenarioChoice).join('|') !== 'base|vesc600') return null;

  function show(id, announce = true) {
    const selected = experience.select(id);
    const openPlot = panels.some((panel) => panel.querySelector('.spectra-details')?.open);
    for (const panel of panels) {
      const active = panel.dataset.recordedScenario === id;
      panel.hidden = !active;
      panel.classList.toggle('is-entering', active && announce);
      const plot = panel.querySelector('.spectra-details');
      if (plot && openPlot) plot.open = true;
    }
    for (const choice of choices) choice.setAttribute('aria-pressed', String(choice.dataset.scenarioChoice === id));
    if (announce) {
      const [first, second] = selected.scenario.snapshots;
      doc.getElementById('scenario-announcement').textContent =
        `Escape speed ${selected.scenario.halo.vesc} kilometers per second. `
        + `Higgsino: ${first.metrics.N_roi_own_sigma.toFixed(3)} expected selected events. `
        + `Exothermic dark matter: ${second.metrics.N_roi_own_sigma.toFixed(3)} expected selected events. `
        + `The observation stays fixed at ${selected.observation.energy_keV} keV.`;
    }
  }
  show('base', false);
  doc.documentElement.classList.add('enhanced');
  doc.querySelector('.scenario-control').hidden = false;
  for (const choice of choices) choice.addEventListener('click', () => show(choice.dataset.scenarioChoice));

  const captions = {
    s1: 'First light · The recoil produces a prompt flash, called S1. Light sensors collect this signal.',
    drift: 'Charge drifts · Electrons released by the interaction move upward through the liquid under an electric field.',
    s2: 'Second light · Extracted electrons produce another flash in the gas, called S2. The two signals help characterize the interaction.',
  };
  const signalButtons = [...doc.querySelectorAll('[data-signal]')];
  doc.querySelector('.signal-controls').hidden = false;
  for (const button of signalButtons) button.addEventListener('click', () => {
    const phase = button.dataset.signal;
    if (!Object.hasOwn(captions, phase)) return;
    doc.querySelector('.detector-scene').dataset.signalPhase = phase;
    doc.querySelector('.signal-caption').textContent = captions[phase];
    for (const b of signalButtons) b.setAttribute('aria-pressed', String(b === button));
  });

  const download = doc.getElementById('download-manifest');
  download.hidden = false;
  download.addEventListener('click', () => {
    const blob = new Blob([JSON.stringify(experience.record(), null, 2) + '\n'], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const anchor = doc.createElement('a');
    anchor.href = url;
    anchor.download = 'lz-validated-scene-manifest.json';
    doc.body.append(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1500);
  });
  return experience;
}
