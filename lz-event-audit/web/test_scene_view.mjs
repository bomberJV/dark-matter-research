import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { createSceneStore } from './scene-view.js';

const manifest = JSON.parse(readFileSync(fileURLToPath(new URL('../scenes/manifest.json', import.meta.url)), 'utf8'));
const html = readFileSync(fileURLToPath(new URL('../scenes/index.html', import.meta.url)), 'utf8');
const fresh = () => structuredClone(manifest);

test('L-04: discrete selection keeps observation identity, values and uncertainty immutable', () => {
  const input = fresh();
  const store = createSceneStore(input);
  const base = store.select('base');
  const scenario = store.select('vesc600');
  assert.strictEqual(base.observation, scenario.observation);
  assert.deepEqual(base.observation, manifest.observation);
  assert.ok(Object.isFrozen(base.observation));
  assert.throws(() => { base.observation.energy_keV = 1; }, TypeError);
  input.observation.energy_keV = 2;
  assert.equal(store.select('base').observation.energy_keV, 248);
  assert.strictEqual(base.common_assumptions, scenario.common_assumptions);
  assert.throws(() => store.select('vesc550'), /Unknown recorded scenario/);
});

test('L-05: the adapter preserves every original qualification, source and numerical result', () => {
  const store = createSceneStore(manifest);
  assert.deepEqual(store.manifest, manifest);
  for (const scenarioId of store.scenarioIds) {
    const view = store.select(scenarioId);
    assert.deepEqual(view.scenario, manifest.scenarios.find((s) => s.id === scenarioId));
    for (const benchmark of view.benchmarks) {
      assert.ok(benchmark.paper_reproduction);
      assert.strictEqual(benchmark, store.manifest.benchmarks.find((b) => b.id === benchmark.id));
    }
  }
  for (const id of ['su-yang-yang', 'dent-newstead-exo', 'gce-simple', 'delepine-khalil']) {
    const benchmark = store.manifest.benchmarks.find((b) => b.id === id);
    assert.ok(benchmark.paper_reproduction, `${id} qualification exists`);
    assert.notEqual(benchmark.paper_reproduction.status, 'reproduced');
  }
});

test('the adapter rejects unknown schema, duplicate IDs, changed benchmark sets and invalid curves', () => {
  const mutations = [
    (m) => { m.schema_version = 'unknown'; },
    (m) => { m.scenarios[1].id = m.scenarios[0].id; },
    (m) => { m.scenarios[0].snapshots[0].benchmark_id = 'unknown'; },
    (m) => { m.scenarios[0].snapshots[0].curve.selected_density_per_roi_keV[0] = Infinity; },
    (m) => { m.scenarios[0].snapshots[0].curve.selected_density_per_roi_keV[0] = -1; },
    (m) => { m.scenarios[0].snapshots[0].curve.energy_keV[1] = m.scenarios[0].snapshots[0].curve.energy_keV[0]; },
  ];
  for (const mutate of mutations) {
    const input = fresh();
    mutate(input);
    assert.throws(() => createSceneStore(input), TypeError);
  }
});

test('L-06: static receipt and progressive view carry exactly the same settings and results', () => {
  const embedded = html.match(/<script id="scene-manifest" type="application\/json">([\s\S]*?)<\/script>/);
  assert.ok(embedded);
  assert.deepEqual(JSON.parse(embedded[1]), manifest);
  const markerPaths = [];
  for (const scenario of manifest.scenarios) {
    const start = html.indexOf(`data-scenario="${scenario.id}"`);
    const end = html.indexOf('</section>', start);
    const section = html.slice(start, end);
    assert.ok(start >= 0);
    assert.match(section, new RegExp(`${scenario.halo.vesc} km/s`));
    assert.ok(!section.slice(0, section.indexOf('>')).includes('hidden'));
    const marker = section.match(/data-observation-energy="([^"]+)" d="([^"]+)"/);
    assert.ok(marker);
    assert.equal(Number(marker[1]), manifest.observation.energy_keV);
    markerPaths.push(marker[2]);
    for (const snapshot of scenario.snapshots) {
      const row = section.match(new RegExp(`<tr data-benchmark="${snapshot.benchmark_id}">([\\s\\S]*?)<\\/tr>`));
      assert.ok(row);
      for (const name of ['N_roi_own_sigma', 'N_sb_own_sigma', 'R_SB', 'dchi2']) {
        const cell = row[1].match(new RegExp(`data-metric="${name}">([^<]+)<\\/td>`));
        assert.ok(cell);
        if (snapshot.metrics[name] === null) assert.equal(cell[1], 'Undefined');
        else assert.equal(Number(cell[1]), Number(snapshot.metrics[name].toPrecision(4)), `${scenario.id}/${snapshot.benchmark_id}/${name}`);
      }
    }
  }
  assert.equal(new Set(markerPaths).size, 1, 'The marker uses the same plot coordinate in both scenarios');
  assert.match(html, /A nuclear-recoil candidate, not a discovery/);
  assert.match(html, /Sideband acceptance is unpublished and assumed to be one/);
  assert.match(html, /no measured event position or detector reconstruction/);
  assert.match(html, /Statistical and systematic uncertainties remain separate/);
  for (const benchmark of manifest.benchmarks) assert.ok(html.includes(benchmark.id));
});
