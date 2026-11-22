import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createExperience, mountExperience } from './experience.js';

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
    const start = html.indexOf(`data-recorded-scenario="${scenario.id}"`);
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

test('interactive mounting switches the rendered snapshot and announces the fixed observation', () => {
  function element(dataset = {}) {
    return { dataset, hidden: false, textContent: '', attrs: {}, handlers: {}, classList: { add() {}, toggle() {} },
      setAttribute(k, v) { this.attrs[k] = v; }, addEventListener(k, fn) { this.handlers[k] = fn; },
      querySelector() { return this.plot; } };
  }
  const panels = ['base', 'vesc600'].map((id) => Object.assign(element({ recordedScenario: id }), { plot: { open: false } }));
  const choices = ['base', 'vesc600'].map((id) => element({ scenarioChoice: id }));
  const signals = ['s1', 'drift', 's2'].map((id) => element({ signal: id }));
  const ids = { 'scene-manifest': { textContent: JSON.stringify(manifest) }, 'scenario-announcement': element(), 'download-manifest': element() };
  const singles = { '.scenario-control': element(), '.signal-controls': element(), '.detector-scene': element(), '.signal-caption': element() };
  const doc = { documentElement: element(), getElementById: (id) => ids[id],
    querySelectorAll: (selector) => ({ '[data-recorded-scenario]': panels, '[data-scenario-choice]': choices, '[data-signal]': signals })[selector],
    querySelector: (selector) => singles[selector] };
  const mounted = mountExperience(doc);
  assert.equal(mounted.current, 'base');
  assert.deepEqual(panels.map((p) => p.hidden), [false, true]);
  panels[0].plot.open = true;
  choices[1].handlers.click();
  assert.equal(mounted.current, 'vesc600');
  assert.deepEqual(panels.map((p) => p.hidden), [true, false]);
  assert.equal(choices[1].attrs['aria-pressed'], 'true');
  assert.equal(panels[1].plot.open, true);
  assert.match(ids['scenario-announcement'].textContent, /93\.740 expected selected events/);
  assert.match(ids['scenario-announcement'].textContent, /stays fixed at 248 keV/);
  signals[2].handlers.click();
  assert.equal(singles['.detector-scene'].dataset.signalPhase, 's2');
  assert.match(singles['.signal-caption'].textContent, /Second light/);
  assert.equal(signals[2].attrs['aria-pressed'], 'true');
  choices[0].handlers.click();
  assert.deepEqual(panels.map((p) => p.hidden), [false, true]);
});

test('invalid manifests leave all static evidence visible', () => {
  assert.equal(mountExperience({ getElementById: () => ({ textContent: '{' }) }), null);
  const invalid = structuredClone(manifest);
  invalid.scenarios[1].id = 'unreviewed';
  assert.throws(() => createExperience(invalid), /two reviewed snapshots/);
});
