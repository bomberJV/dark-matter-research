import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createExperience, createSignalPlayback, mountExperience } from './experience.js';

const manifest = JSON.parse(readFileSync(new URL('../scenes/manifest.json', import.meta.url), 'utf8'));
const html = readFileSync(new URL('../scenes/experience.html', import.meta.url), 'utf8');

test('guided scenario changes never change the observation, parameters or stored results', () => {
  const model = createExperience(manifest);
  const observed = model.observation;
  for (const id of ['vesc600', 'base', 'vesc600', 'base']) {
    const view = model.select(id);
    assert.strictEqual(view.observation, observed);
    assert.deepEqual(view.scenario, manifest.scenarios.find((s) => s.id === id));
    assert.equal(model.current, id);
  }
  assert.throws(() => model.select('vesc550'), /Unknown recorded scenario/);
  assert.equal(model.current, 'base');
  assert.throws(() => { model.observation.energy_keV = 1; }, TypeError);
  assert.deepEqual(model.record(), manifest);
});

test('standalone download payload preserves the complete qualified manifest', () => {
  const embedded = html.match(/<script id="scene-manifest" type="application\/json">([\s\S]*?)<\/script>/);
  assert.ok(embedded);
  assert.deepEqual(JSON.parse(embedded[1]), manifest);
  for (const benchmark of manifest.benchmarks) {
    assert.ok(html.includes(benchmark.id));
    assert.ok(html.includes(benchmark.paper_reproduction.status));
  }
  assert.match(html, /Numerical reproduction ≠ paper reproduction/);
  assert.match(html, /acceptance is unpublished and assumed to be one/);
  assert.match(html, /A candidate, not a discovery/);
  assert.match(html, /NOT MEASURED GEOMETRY/);
  assert.match(html, /Statistical and systematic uncertainties remain separate/);
});

test('static counts, grids and curve markers agree in both scenarios without JavaScript', () => {
  const markers = [];
  for (const scenario of manifest.scenarios) {
    const start = html.indexOf(`<section class="snapshot-state" data-recorded-scenario="${scenario.id}"`);
    const end = html.indexOf('</section>', start);
    const section = html.slice(start, end);
    assert.ok(start > 0);
    assert.ok(!section.slice(0, section.indexOf('>')).includes('hidden'));
    for (const shot of scenario.snapshots) {
      const article = section.match(new RegExp(`<article class="model" data-benchmark="${shot.benchmark_id}">([\\s\\S]*?)<\\/article>`))[1];
      const count = Number(article.match(/data-expected-count="([^"]+)"/)[1]);
      assert.equal(count, shot.metrics.N_roi_own_sigma);
      assert.equal(Number(article.match(/data-metric="N_roi_own_sigma">([^<]+)/)[1]), Number(count.toPrecision(4)));
      const fills = [...article.matchAll(/class="grid-filled"[^>]*width="([^"]+)"/g)].map((m) => Number(m[1]));
      assert.ok(Math.abs(fills.reduce((sum, w) => sum + w / 12, 0) - count) < 1e-8);
      assert.equal([...article.matchAll(/class="grid-empty"/g)].length, 100);
    }
    markers.push(section.match(/data-observation-energy="248" d="([^"]+)"/)[1]);
  }
  assert.equal(new Set(markers).size, 1);
  assert.doesNotMatch(html, /<script[^>]+src=|<link[^>]+stylesheet|<img[^>]+src=/);
  assert.match(html, /prefers-reduced-motion:reduce/);
});

function documentFixture() {
  function element(dataset = {}) {
    return { dataset, hidden: false, disabled: false, textContent: '', attrs: {}, handlers: {}, classList: { add() {}, toggle() {} },
      setAttribute(k, v) { this.attrs[k] = v; }, addEventListener(k, fn) { this.handlers[k] = fn; },
      removeAttribute(k) { delete this.attrs[k]; }, focus() { this.focused = true; }, scrollIntoView() { this.scrolled = true; },
      querySelector() { return this.plot; } };
  }
  const panels = ['base', 'vesc600'].map((id) => Object.assign(element({ recordedScenario: id }), { plot: { open: false } }));
  const choices = ['base', 'vesc600'].map((id) => element({ scenarioChoice: id }));
  const signals = ['s1', 'drift', 's2'].map((id) => element({ signal: id }));
  const guesses = ['higgsino', 'exothermic', 'similar'].map((id) => element({ prediction: id }));
  const sidebands = ['base', 'vesc600'].map((id) => element({ sidebandScenario: id }));
  const captions = ['base', 'vesc600'].map((id) => element({ haloCaption: id }));
  const progress = ['predict', 'test', 'check'].map((id) => element({ progress: id }));
  const cards = ['higgsino', 'exothermic'].map((id) => element({ hypothesis: id }));
  // Ground every id in the generated HTML: missing controls cannot be hidden by the fixture.
  const ids = Object.fromEntries([...html.matchAll(/\bid="([^"]+)"/g)].map((m) => [m[1], element()]));
  ids['scene-manifest'].textContent = JSON.stringify(manifest);
  const selectors = ['.scenario-control', '.signal-controls', '.detector-scene', '.signal-caption', '.halo-stage', '.signal-playback', '.prediction-console', '.journey-progress', '.skip'];
  const singles = Object.fromEntries(selectors.map((s) => {
    assert.ok(new RegExp(`class="[^\"]*\\b${s.slice(1)}\\b`).test(html), `HTML includes ${s}`);
    return [s, element()];
  }));
  const media = { matches: false, addEventListener() {} };
  const doc = { documentElement: element(), handlers: {}, visibilityState: 'visible',
    addEventListener(k, fn) { this.handlers[k] = fn; }, getElementById: (id) => ids[id], defaultView: { matchMedia: () => media },
    querySelectorAll: (selector) => ({ '[data-recorded-scenario]': panels, '[data-scenario-choice]': choices, '[data-signal]': signals,
      '[data-prediction]': guesses, '[data-sideband-scenario]': sidebands, '[data-halo-caption]': captions, '[data-progress]': progress, '[data-hypothesis]': cards })[selector],
    querySelector: (selector) => singles[selector] };
  return { doc, ids, singles, panels, choices, signals, guesses, sidebands, captions, progress, media };
}

test('interactive journey records a guess, reveals fixed results, opens the wider check and resets', () => {
  const { doc, ids, singles, panels, choices, signals, guesses, sidebands, progress } = documentFixture();
  const mounted = mountExperience(doc);
  assert.equal(mounted.current, 'base');
  assert.equal(ids.experiment.hidden, true);
  assert.equal(ids['wider-check'].hidden, true);
  assert.equal(ids['test-prediction'].disabled, true);
  assert.deepEqual(panels.map((p) => p.hidden), [false, true]);
  guesses[1].handlers.click();
  assert.equal(mounted.state.prediction, 'exothermic');
  assert.equal(ids['test-prediction'].disabled, false);
  assert.equal(ids['prediction-verdict'].hidden, true);
  ids['test-prediction'].handlers.click();
  assert.equal(ids.experiment.hidden, false);
  assert.equal(ids['experiment-title'].focused, true);
  assert.equal(ids['reported-measurement'].hidden, false);
  panels[0].plot.open = true;
  choices[1].handlers.click();
  assert.equal(mounted.current, 'vesc600');
  assert.deepEqual(panels.map((p) => p.hidden), [true, false]);
  assert.equal(choices[1].attrs['aria-pressed'], 'true');
  assert.equal(panels[1].plot.open, true);
  assert.match(ids['scenario-announcement'].textContent, /93\.740 expected selected events/);
  assert.match(ids['scenario-announcement'].textContent, /stays fixed at 248 keV/);
  assert.match(ids['prediction-verdict'].textContent, /You expected B/);
  assert.match(ids['prediction-verdict'].textContent, /144 times larger/);
  assert.ok(guesses.every((g) => g.disabled));
  assert.equal(ids['prediction-verdict'].focused, true);
  ids['open-check'].handlers.click();
  assert.equal(ids['wider-check'].hidden, false);
  assert.deepEqual(sidebands.map((p) => p.hidden), [true, false]);
  assert.equal(progress[2].attrs['aria-current'], 'step');
  signals[2].handlers.click();
  assert.equal(singles['.detector-scene'].dataset.signalPhase, 's2');
  assert.match(singles['.signal-caption'].textContent, /Second light/);
  assert.equal(signals[2].attrs['aria-pressed'], 'true');
  choices[0].handlers.click();
  assert.deepEqual(panels.map((p) => p.hidden), [false, true]);
  assert.deepEqual(sidebands.map((p) => p.hidden), [false, true]);
  assert.equal(mounted.state.prediction, 'exothermic');
  ids['reset-investigation'].handlers.click();
  assert.equal(ids.experiment.hidden, true);
  assert.equal(ids['wider-check'].hidden, true);
  assert.equal(mounted.state.prediction, null);
  assert.equal(ids['predictions-title'].focused, true);
  assert.ok(guesses.every((g) => !g.disabled));
});

test('every guess and the optional skip path lead to exactly the same physics', () => {
  for (const guess of ['higgsino', 'exothermic', 'similar', null]) {
    const model = createExperience(manifest);
    const observed = model.observation;
    assert.throws(() => model.openCheck(), /Reveal/);
    assert.throws(() => model.predict('a winning theory'), /Unknown prediction/);
    model.predict(guess);
    model.beginTest();
    assert.deepEqual(model.select('vesc600').scenario, manifest.scenarios[1]);
    assert.throws(() => model.predict('higgsino'), /Reset/);
    model.openCheck();
    model.select('base');
    assert.throws(() => model.predict(null), /Reset/);
    assert.equal(model.state.prediction, guess);
    model.reset();
    assert.deepEqual(model.state, { current: 'base', prediction: null, revealed: false, labOpen: false, checkOpen: false });
    assert.strictEqual(model.observation, observed);
    assert.deepEqual(model.record(), manifest);
  }
});

test('sideband bars conserve expected counts and preserve the measured energy marker', () => {
  const energyMarkers = [];
  for (const scenario of manifest.scenarios) {
    const start = html.indexOf(`<div class="sideband-state" data-sideband-scenario="${scenario.id}">`);
    const next = html.indexOf('<div class="sideband-state"', start + 1);
    const block = html.slice(start, next < 0 ? html.indexOf('<p class="acceptance-note">', start) : next);
    assert.ok(start > 0);
    assert.ok(!block.slice(0, block.indexOf('>')).includes('hidden'));
    energyMarkers.push(block.match(/data-fixed-energy="248" d="([^"]+)"/)[1]);
    const bars = [...block.matchAll(/data-sideband-count="([^"]+)" width="([^"]+)"/g)];
    assert.equal(bars.length, 2);
    bars.forEach((bar, i) => {
      assert.equal(Number(bar[1]), scenario.snapshots[i].metrics.N_sb_own_sigma);
      assert.ok(Math.abs(Number(bar[2]) / 10 - Number(bar[1])) < 1e-8);
    });
  }
  assert.equal(new Set(energyMarkers).size, 1);
  assert.match(html, /No high-energy event data are plotted here/);
  assert.match(html, /not a sampled distribution or a rate calculation/);
  assert.match(html, /This export alone cannot declare a winner/);
});

function signalFixture(reduced = false) {
  const pending = new Map(), frames = [];
  let nextId = 0, completions = 0;
  const signal = createSignalPlayback({ onFrame: (frame) => frames.push(frame), onComplete: () => { completions++; },
    reducedMotion: () => reduced, schedule(fn) { pending.set(++nextId, fn); return nextId; }, cancel(id) { pending.delete(id); } });
  return { signal, frames, pending, get completions() { return completions; },
    tick() { const [id, fn] = pending.entries().next().value; pending.delete(id); fn(); } };
}

test('signal illustration supports pause, resume, replay and manual steps without orphan timers', () => {
  const f = signalFixture();
  f.signal.play();
  assert.deepEqual(f.frames, ['s1']);
  assert.equal(f.pending.size, 1);
  f.signal.play();
  assert.equal(f.pending.size, 1);
  f.signal.pause();
  assert.equal(f.pending.size, 0);
  f.signal.play(); f.tick();
  assert.equal(f.frames.at(-1), 'drift');
  f.tick(); assert.equal(f.frames.at(-1), 's2');
  f.tick(); assert.equal(f.frames.at(-1), 'observed');
  assert.equal(f.signal.complete, true);
  assert.equal(f.completions, 1);
  assert.equal(f.pending.size, 0);
  f.signal.play(); assert.equal(f.frames.at(-1), 's1');
  f.signal.select('s2');
  assert.equal(f.pending.size, 0);
  assert.equal(f.signal.complete, true);
  f.signal.play(); assert.equal(f.frames.at(-1), 's1');
  f.signal.dispose(); assert.equal(f.pending.size, 0);
  assert.throws(() => f.signal.select('unmeasured'), /Unknown illustration/);
});

test('reduced motion reaches the observation immediately without timed animation', () => {
  const f = signalFixture(true);
  f.signal.play();
  assert.deepEqual(f.frames, ['observed']);
  assert.equal(f.pending.size, 0);
  assert.equal(f.completions, 1);
  const { doc, ids, media } = documentFixture();
  media.matches = true;
  mountExperience(doc);
  ids['play-signal'].handlers.click();
  assert.equal(ids['reported-measurement'].hidden, false);
  assert.equal(ids['start-investigation'].hidden, false);
  assert.equal(ids['motion-toggle'].disabled, true);
  assert.equal(doc.documentElement.dataset.motion, 'paused');
});

test('skip prediction still opens the full exploration and evidence remains accessible', () => {
  const { doc, ids, choices } = documentFixture();
  const model = mountExperience(doc);
  ids['skip-prediction'].handlers.click();
  assert.equal(model.state.prediction, null);
  assert.equal(ids.experiment.hidden, false);
  assert.equal(ids.evidence.hidden, false);
  choices[1].handlers.click();
  assert.doesNotMatch(ids['prediction-verdict'].textContent, /Your prediction held|You expected/);
  ids['open-check'].handlers.click();
  assert.equal(ids['wider-check'].hidden, false);
});

test('mobile signal controls keep the illustration and reported energy reachable; pause cancels playback', () => {
  const { doc, ids, singles } = documentFixture();
  doc.defaultView.innerWidth = 390;
  mountExperience(doc);
  ids['play-signal'].handlers.click();
  assert.equal(singles['.detector-scene'].focused, true);
  assert.equal(singles['.detector-scene'].dataset.playing, 'true');
  ids['motion-toggle'].handlers.click();
  assert.equal(doc.documentElement.dataset.motion, 'paused');
  assert.equal(singles['.detector-scene'].dataset.playing, 'false');
  ids['motion-toggle'].handlers.click();
  assert.equal(singles['.detector-scene'].dataset.playing, 'true');
  doc.visibilityState = 'hidden'; doc.handlers.visibilitychange();
  assert.equal(singles['.detector-scene'].dataset.playing, 'false');
  ids['skip-signal'].handlers.click();
  assert.equal(ids['signal-reading'].hidden, false);
  ids['signal-next'].handlers.click({ preventDefault() {} });
  assert.equal(ids['predictions-title'].focused, true);
});

test('invalid manifests leave all static evidence visible', () => {
  assert.equal(mountExperience({ getElementById: () => ({ textContent: '{' }) }), null);
  const invalid = structuredClone(manifest);
  invalid.scenarios[1].id = 'unreviewed';
  assert.throws(() => createExperience(invalid), /two reviewed snapshots/);
});
