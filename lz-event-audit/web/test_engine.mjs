// Parity tests: engine.js against the Python audit (rates.py / audit.py).
// Run: node --test test_engine.mjs
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import {
  predict, sigmaForOneEvent, timingFactor, deltaForOneEvent, kinematicallyAllowed,
  DEFAULT_HALO, LZ_HALO_FIXED, DEFAULT_DET,
} from './engine.js';

const HERE = dirname(fileURLToPath(import.meta.url));
const FULL = { n: 2400, nTime: 48 };
const FAST = { n: 1200, nTime: 24 };

function parseCSV(text) {
  const rows = [];
  let row = [], field = '', q = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (q) {
      if (ch === '"' && text[i + 1] === '"') { field += '"'; i++; }
      else if (ch === '"') q = false;
      else field += ch;
    } else if (ch === '"') q = true;
    else if (ch === ',') { row.push(field); field = ''; }
    else if (ch === '\n') { row.push(field); rows.push(row); row = []; field = ''; }
    else if (ch !== '\r') field += ch;
  }
  if (field || row.length) { row.push(field); rows.push(row); }
  const [head, ...body] = rows;
  return body.filter((r) => r.length === head.length).map((r) => Object.fromEntries(head.map((h, i) => [h, r[i]])));
}

const bench = parseCSV(readFileSync(join(HERE, '..', 'benchmarks.csv'), 'utf8'));
const results = Object.fromEntries(parseCSV(readFileSync(join(HERE, '..', 'results', 'benchmarks_common.csv'), 'utf8')).map((r) => [r.id, r]));

let worst = { rel: 0, what: '' };
function close(js, py, label, { rel = 0.02, abs = 0 } = {}) {
  if (py === '' || py === undefined || py === 'None') return;
  const p = Number(py);
  if (!Number.isFinite(p)) { assert.ok(!Number.isFinite(js), `${label}: expected non-finite`); return; }
  if (abs) {
    assert.ok(Math.abs(js - p) <= abs, `${label}: js ${js} vs py ${p} (abs tol ${abs})`);
    return;
  }
  if (Math.abs(p) < 1e-6) return;
  const r = Math.abs(js / p - 1);
  if (r > worst.rel) worst = { rel: r, what: `${label}: js ${js.toPrecision(5)} py ${p}` };
  assert.ok(r <= rel, `${label}: js ${js} vs py ${p} (rel ${r.toFixed(4)})`);
}

const modelOf = (b) => ({ m: Number(b.m_chi_GeV), delta: Number(b.delta_keV), coupling: b.coupling,
  sigma_n: b.sigma_n_cm2 ? Number(b.sigma_n_cm2) : undefined });

for (const b of bench) {
  test(`parity: ${b.id}`, () => {
    const r = results[b.id];
    assert.ok(r, 'present in results CSV');
    const mod = modelOf(b);
    assert.ok(kinematicallyAllowed(mod, DEFAULT_HALO));
    const p = predict(mod, DEFAULT_HALO, DEFAULT_DET, FULL);
    close(p.ratio_sb, r.R_SB, 'R_SB');
    close(p.dchi2, r.dchi2, 'dchi2', { abs: 0.02 });
    close(p.dchi2_roi, r.dchi2_roi_only, 'dchi2_roi_only', { abs: 0.02 });
    close(p.N_low / p.N_roi, r.f_low, 'f_low');
    if (mod.sigma_n) {
      close(p.N_roi, r.N_roi_own_sigma, 'N_roi_own_sigma');
      close(predict(mod, LZ_HALO_FIXED, DEFAULT_DET, FULL).N_roi, r.N_roi_own_sigma_vE254, 'N_roi_own_sigma_vE254');
    }
    close(timingFactor(mod, DEFAULT_HALO, DEFAULT_DET, FULL), r.timing_factor, 'timing_factor');
  });
}

test('interactive settings (n 1200, 24 time samples) track the full grid', () => {
  for (const b of bench) {
    const mod = modelOf(b);
    const f = predict(mod, DEFAULT_HALO, DEFAULT_DET, FULL);
    const s = predict(mod, DEFAULT_HALO, DEFAULT_DET, FAST);
    assert.ok(Math.abs(s.ratio_sb / f.ratio_sb - 1) <= 0.05, `${b.id} R_SB ${s.ratio_sb} vs ${f.ratio_sb}`);
    assert.ok(Math.abs(s.N_roi / f.N_roi - 1) <= 0.05, `${b.id} N_roi ${s.N_roi} vs ${f.N_roi}`);
    assert.ok(Math.abs(s.dchi2 - f.dchi2) <= 0.1, `${b.id} dchi2 ${s.dchi2} vs ${f.dchi2}`);
  }
});

test('anchor: Baer & Barger sigma_p for one event (validate.py)', () => {
  const rows = [[300, -300, 1.448e-45], [500, -275, 2.22e-45], [500, -350, 3.81e-45], [800, -350, 6.70e-45], [1000, -400, 1.30e-44]];
  for (const [m, d, s] of rows) close(sigmaForOneEvent({ m, delta: d, coupling: 'Z' }, LZ_HALO_FIXED, DEFAULT_DET, FULL), s, `BB ${m}/${d}`, { rel: 0.01 });
});

test('anchor: Rodd et al. higgsino delta_1, year-averaged, vesc 544 -> 375.3 keV', () => {
  const d = deltaForOneEvent({ m: 1100, coupling: 'QW', sigma_n: 7.3e-39 }, DEFAULT_HALO, DEFAULT_DET, FULL);
  assert.ok(Math.abs(d - 375.3) < 0.3, `delta_1 ${d}`);
});

test('anchor: Di Mauro N_ROI 0.94', () => {
  const p = predict({ m: 1000, delta: 297.05, coupling: 'A', sigma_n: 6.5e-43 }, DEFAULT_HALO, DEFAULT_DET, FULL);
  close(p.N_roi, 0.9424, 'Di Mauro N_ROI', { rel: 0.01 });
});

test('report worst deviation', () => {
  console.log(`worst relative deviation: ${(100 * worst.rel).toFixed(2)}% (${worst.what})`);
});
