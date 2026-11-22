import { createSceneStore } from './scene-view.js';

// Choices affect the narrative only. They never change a calculation or observation.
export function createExperience(manifest) {
  const store = createSceneStore(manifest);
  if (store.scenarioIds.join('|') !== 'base|vesc600') throw new TypeError('Expected the two reviewed snapshots');
  const selectedIds = store.select('base').scenario.snapshots.map((s) => s.benchmark_id);
  if (selectedIds.join('|') !== 'rodd-higgsino|baer-barger-300') throw new TypeError('Unexpected narrative benchmarks');
  let current = 'base', prediction = null, revealed = false, labOpen = false, checkOpen = false;
  return Object.freeze({
    get current() { return current; },
    get observation() { return store.manifest.observation; },
    get state() { return Object.freeze({ current, prediction, revealed, labOpen, checkOpen }); },
    predict(choice) {
      if (revealed) throw new RangeError('Reset the investigation before making a new prediction');
      if (![null, 'higgsino', 'exothermic', 'similar'].includes(choice)) throw new RangeError('Unknown prediction');
      prediction = choice;
    },
    beginTest() { labOpen = true; },
    select(id) {
      const view = store.select(id);
      current = id;
      labOpen = true;
      if (id === 'vesc600') revealed = true;
      return view;
    },
    openCheck() {
      if (!revealed) throw new RangeError('Reveal the changed snapshot before opening the wider check');
      checkOpen = true;
    },
    reset() { current = 'base'; prediction = null; revealed = false; labOpen = false; checkOpen = false; },
    record() { return store.manifest; },
  });
}

// Illustration timing only. None of these durations represents measured detector timing.
export function createSignalPlayback({ onFrame, onComplete, onPlayingChange = () => {},
  reducedMotion = () => false, schedule = setTimeout, cancel = clearTimeout }) {
  const frames = ['s1', 'drift', 's2'];
  const durations = [1200, 2100, 1500];
  let index = -1, timer = null, playing = false;
  function stop() {
    if (timer !== null) cancel(timer);
    timer = null;
    playing = false;
    onPlayingChange(false);
  }
  function finish() { stop(); index = frames.length; onFrame('observed'); onComplete(); }
  function advance() {
    timer = null;
    if (!playing) return;
    index += 1;
    if (index >= frames.length) { finish(); return; }
    onFrame(frames[index]);
    timer = schedule(advance, durations[index]);
  }
  return Object.freeze({
    get playing() { return playing; },
    get complete() { return index === frames.length; },
    play() {
      if (playing) return;
      if (reducedMotion()) { finish(); return; }
      playing = true;
      onPlayingChange(true);
      if (index < 0 || index >= frames.length) { index = -1; advance(); }
      else { onFrame(frames[index]); timer = schedule(advance, durations[index]); }
    },
    pause: stop,
    finish,
    select(phase) {
      const target = frames.indexOf(phase);
      if (target < 0) throw new RangeError('Unknown illustration phase');
      stop(); index = target; onFrame(phase);
      if (phase === 's2') { index = frames.length; onComplete(); }
    },
    dispose: stop,
  });
}

export function mountExperience(doc) {
  const embedded = doc.getElementById('scene-manifest');
  if (!embedded) return null;
  let experience;
  try { experience = createExperience(JSON.parse(embedded.textContent)); }
  catch { return null; }
  const all = (selector) => [...doc.querySelectorAll(selector)];
  const el = (id) => doc.getElementById(id);
  const panels = all('[data-recorded-scenario]');
  const choices = all('[data-scenario-choice]');
  const guesses = all('[data-prediction]');
  const sidebands = all('[data-sideband-scenario]');
  const signalButtons = all('[data-signal]');
  if (panels.map((p) => p.dataset.recordedScenario).join('|') !== 'base|vesc600'
      || choices.map((p) => p.dataset.scenarioChoice).join('|') !== 'base|vesc600'
      || sidebands.map((p) => p.dataset.sidebandScenario).join('|') !== 'base|vesc600') return null;

  const media = doc.defaultView?.matchMedia?.('(prefers-reduced-motion: reduce)');
  let motionPaused = Boolean(media?.matches), motionWasPlaying = false;
  const predictionNames = { higgsino: 'A · Higgsino', exothermic: 'B · Exothermic dark matter', similar: 'Similar changes' };
  const captions = {
    idle: 'Follow the illustrated sequence: first light, drifting charge, then second light. The signals let the experiment characterize a recoil.',
    s1: '01 / First light · The recoil produces a prompt flash, called S1. Light sensors collect the signal.',
    drift: '02 / Charge drifts · Released electrons move upward through the liquid under an electric field.',
    s2: '03 / Second light · Extracted electrons produce another flash in the gas, called S2. The two signals help characterize the interaction.',
    observed: 'The illustrated sequence is complete. The reported candidate’s reconstructed energy is now shown. No measured waveform, position or timing is being replayed.',
  };
  const reduced = () => Boolean(media?.matches);
  function focusAndScroll(element) {
    element?.focus?.({ preventScroll: true });
    element?.scrollIntoView?.({ block: 'start', behavior: reduced() ? 'auto' : 'smooth' });
  }
  function updateMotion() {
    doc.documentElement.dataset.motion = motionPaused ? 'paused' : 'running';
    el('motion-toggle').disabled = reduced();
    el('motion-toggle').textContent = reduced() ? 'Reduced motion on' : motionPaused ? 'Resume illustration motion' : 'Pause illustration motion';
    el('motion-toggle').setAttribute('aria-pressed', String(motionPaused));
  }
  function completeSignal() {
    el('reported-measurement').hidden = false;
    el('start-investigation').hidden = false;
    el('signal-reading').hidden = false;
    el('skip-signal').hidden = true;
    doc.querySelector('.detector-scene').classList.add('signal-complete');
  }
  const playback = createSignalPlayback({
    reducedMotion: reduced,
    onFrame(phase) {
      doc.querySelector('.detector-scene').dataset.signalPhase = phase;
      doc.querySelector('.detector-scene').dataset.signalPaused = 'false';
      doc.querySelector('.signal-caption').textContent = captions[phase];
      for (const b of signalButtons) b.setAttribute('aria-pressed', String(b.dataset.signal === phase));
    },
    onComplete() { completeSignal(); el('play-signal').textContent = 'Replay the signal ↺'; },
    onPlayingChange(playing) {
      doc.querySelector('.detector-scene').dataset.playing = String(playing);
      doc.querySelector('.detector-scene').dataset.signalPaused = String(!playing);
      el('play-signal').textContent = playing ? 'Pause the signal Ⅱ' : playback.complete ? 'Replay the signal ↺' : 'Resume the signal ▶';
    },
  });

  function verdictText() {
    const guess = experience.state.prediction;
    if (!experience.state.revealed) return '';
    const intro = guess === 'higgsino' ? 'Your prediction held.'
      : guess === 'exothermic' ? 'You expected B to change more. Here, A changes far more.'
        : guess === 'similar' ? 'You expected similar changes. The two responses are very different.'
          : 'The two responses are very different.';
    const [base, changed] = experience.record().scenarios;
    const factor = changed.snapshots[0].metrics.N_roi_own_sigma / base.snapshots[0].metrics.N_roi_own_sigma;
    const percent = (changed.snapshots[1].metrics.N_roi_own_sigma / base.snapshots[1].metrics.N_roi_own_sigma - 1) * 100;
    return `${intro} Raising the cutoff from 544 to 600 km/s makes the higgsino expectation about ${factor.toFixed(0)} times larger. The exothermic expectation changes by ${percent.toFixed(2)}%. This tests sensitivity to an assumption, not which theory is true.`;
  }
  function update() {
    const state = experience.state;
    el('experiment').hidden = !state.labOpen;
    el('wider-check').hidden = !state.checkOpen;
    el('next-check').hidden = !state.revealed || state.checkOpen;
    el('prediction-verdict').hidden = !state.revealed;
    el('prediction-verdict').textContent = verdictText();
    el('prediction-ticket').hidden = !state.labOpen;
    el('prediction-ticket').textContent = state.prediction ? `Your prediction: ${predictionNames[state.prediction]}.` : 'Exploring without a prediction.';
    el('prediction-status').textContent = state.revealed ? 'Your prediction is held here with the result. Reset the investigation to begin again.'
      : state.prediction ? `Your prediction: ${predictionNames[state.prediction]}. Now test the assumption.`
        : 'Choose an expectation, then test it. You are predicting sensitivity, not choosing a winning theory.';
    el('test-prediction').disabled = !state.prediction || state.revealed;
    el('skip-prediction').hidden = state.revealed;
    for (const g of guesses) {
      g.disabled = state.revealed;
      g.setAttribute('aria-pressed', String(g.dataset.prediction === state.prediction));
    }
    for (const card of all('[data-hypothesis]')) card.classList.toggle('chosen', card.dataset.hypothesis === state.prediction);
    for (const panel of panels) panel.hidden = panel.dataset.recordedScenario !== state.current;
    for (const s of sidebands) s.hidden = s.dataset.sidebandScenario !== state.current;
    for (const choice of choices) choice.setAttribute('aria-pressed', String(choice.dataset.scenarioChoice === state.current));
    doc.querySelector('.halo-stage').dataset.haloScenario = state.current;
    for (const caption of all('[data-halo-caption]')) caption.hidden = caption.dataset.haloCaption !== state.current;
    const active = state.checkOpen ? 'check' : state.labOpen ? 'test' : 'predict';
    for (const step of all('[data-progress]')) {
      if (step.dataset.progress === active) step.setAttribute('aria-current', 'step');
      else step.removeAttribute('aria-current');
    }
  }
  function show(id) {
    const firstReveal = id === 'vesc600' && !experience.state.revealed;
    const selected = experience.select(id);
    const openPlot = panels.some((panel) => panel.querySelector('.spectra-details')?.open);
    for (const panel of panels) {
      panel.classList.toggle('is-entering', panel.dataset.recordedScenario === id);
      if (openPlot) panel.querySelector('.spectra-details').open = true;
    }
    update();
    const [first, second] = selected.scenario.snapshots;
    el('scenario-announcement').textContent =
      `Escape speed ${selected.scenario.halo.vesc} kilometers per second. `
      + `Higgsino: ${first.metrics.N_roi_own_sigma.toFixed(3)} expected selected events. `
      + `Exothermic dark matter: ${second.metrics.N_roi_own_sigma.toFixed(3)} expected selected events. `
      + `The observation stays fixed at ${selected.observation.energy_keV} keV.`;
    if (firstReveal) focusAndScroll(el('prediction-verdict'));
  }
  function beginTest(skip = false) {
    playback.finish();
    if (skip) experience.predict(null);
    experience.beginTest();
    update();
    focusAndScroll(el('experiment-title'));
  }

  // Enhance only after the data contract and required scenario elements are valid.
  doc.documentElement.classList.add('enhanced');
  for (const selector of ['.signal-playback', '.signal-controls', '.prediction-console', '.scenario-control', '.journey-progress']) doc.querySelector(selector).hidden = false;
  el('reset-investigation').hidden = false;
  el('reported-measurement').hidden = true;
  el('start-investigation').hidden = true;
  el('signal-reading').hidden = true;
  doc.querySelector('.detector-scene').dataset.signalPhase = 'idle';
  doc.querySelector('.signal-caption').textContent = captions.idle;
  for (const b of signalButtons) b.setAttribute('aria-pressed', 'false');
  updateMotion();
  update();

  for (const choice of choices) choice.addEventListener('click', () => show(choice.dataset.scenarioChoice));
  for (const guess of guesses) guess.addEventListener('click', () => { experience.predict(guess.dataset.prediction); update(); });
  for (const button of signalButtons) button.addEventListener('click', () => playback.select(button.dataset.signal));
  el('play-signal').addEventListener('click', () => {
    if (playback.playing) playback.pause();
    else {
      if (!reduced()) { motionPaused = false; updateMotion(); }
      if (doc.defaultView?.innerWidth <= 760) focusAndScroll(doc.querySelector('.detector-scene'));
      playback.play();
    }
  });
  el('skip-signal').addEventListener('click', () => playback.finish());
  el('start-investigation').addEventListener('click', (event) => { event.preventDefault(); playback.finish(); focusAndScroll(el('predictions-title')); });
  el('signal-next').addEventListener('click', (event) => { event.preventDefault(); playback.finish(); focusAndScroll(el('predictions-title')); });
  doc.querySelector('.skip').addEventListener('click', (event) => { event.preventDefault(); playback.finish(); focusAndScroll(el('predictions-title')); });
  el('test-prediction').addEventListener('click', () => beginTest());
  el('skip-prediction').addEventListener('click', () => beginTest(true));
  el('open-check').addEventListener('click', () => { experience.openCheck(); update(); focusAndScroll(el('check-title')); });
  el('reset-investigation').addEventListener('click', () => {
    playback.finish(); experience.reset(); update();
    el('scenario-announcement').textContent = 'Investigation reset. The reported observation is unchanged.';
    focusAndScroll(el('predictions-title'));
  });
  el('motion-toggle').addEventListener('click', () => {
    motionPaused = !motionPaused;
    if (motionPaused) { motionWasPlaying = playback.playing; if (motionWasPlaying) playback.pause(); }
    else if (motionWasPlaying && !playback.complete) playback.play();
    updateMotion();
  });
  media?.addEventListener?.('change', () => { motionPaused = reduced(); if (motionPaused) playback.pause(); updateMotion(); });
  doc.addEventListener('visibilitychange', () => { if (doc.visibilityState === 'hidden' && playback.playing) playback.pause(); });

  const download = el('download-manifest');
  download.hidden = false;
  download.addEventListener('click', () => {
    const blob = new Blob([JSON.stringify(experience.record(), null, 2) + '\n'], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const anchor = doc.createElement('a');
    anchor.href = url; anchor.download = 'lz-validated-scene-manifest.json';
    doc.body.append(anchor); anchor.click(); anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1500);
  });
  return experience;
}
