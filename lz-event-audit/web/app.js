import {
  predict, timingFactor, kinematicallyAllowed,
  DEFAULT_HALO, DEFAULT_DET, EVENT_PHASE,
} from './engine.js';

const $ = (s) => document.querySelector(s);
const COL = { mint: '#66d9cb', peach: '#ffb784', ink: '#edf0e4', muted: '#a5b8aa', line: '#34473a', red: '#d06a6a', bg: '#0d150f' };
const OPTS = { n: 1200, nTime: 24 };

const state = {
  bench: 'rodd-higgsino', m: 1100, delta: 377, coupling: 'QW', norm: 'one', sigma: 7.3e-39,
  rho: 0.3, vesc: 544, v0: 238, vE: 250.2, time: 'avg', escale: 1, sbHi: 590, logy: false,
};
let BENCH = [];
// Each paper's own halo, where stated (vE marked 'assumed' where the paper gives none).
const LZF = { rho: 0.3, v0: 238, vesc: 544, vE: 254, time: 'fixed' };
const COMMON = { rho: 0.3, v0: 238, vesc: 544, vE: 250.2, time: 'avg' };
const PAPER_HALO = {
  'su-yang-yang': [{ rho: 0.3, v0: 220, vesc: 544, vE: 220, time: 'fixed' }, 'v₀ 220, escape 544, Earth 220 km/s'],
  'fan-reece': [{ rho: 0.4, v0: 220, vesc: 540, vE: 232, time: 'fixed' }, 'ρ 0.4, v₀ 220, escape 540 km/s; Earth speed not stated, 232 assumed'],
  'freese-theo-1000': [LZF, 'LZ conventions (values not stated; LZ fixed speed assumed)'],
  'freese-theo-1100': [LZF, 'LZ conventions (values not stated; LZ fixed speed assumed)'],
  'di-mauro': [COMMON, 'same as the common halo'],
  'rodd-higgsino': [COMMON, 'same as the common halo'],
  'dent-newstead-endo': [{ rho: 0.3, v0: 238, vesc: 544, vE: 250, time: 'fixed' }, 'v₀ 238, escape 544, lab 250 km/s'],
  'dent-newstead-exo': [{ rho: 0.3, v0: 238, vesc: 544, vE: 250, time: 'fixed' }, 'v₀ 238, escape 544, lab 250 km/s'],
  'fan-he-bestfit': [{ rho: 0.3, v0: 219, vesc: 543, vE: 219, time: 'fixed' }, 'v₀ = Earth 219, escape 543 km/s'],
  'delepine-khalil': [{ rho: 0.3, v0: 238, vesc: 544, vE: 232, time: 'fixed' }, 'v₀ 238, escape 544, Earth 232 km/s'],
  'mahapatra-paul': [{ rho: 0.3, v0: 220, vesc: 540, vE: 232, time: 'fixed' }, 'v₀ 220, escape 540, Earth 232 km/s'],
  'freeze-in-lepto': [COMMON, 'same as the common halo'],
  'freeze-in-univ': [COMMON, 'same as the common halo'],
};
['baer-barger-300', 'baer-barger-500a', 'baer-barger-500b', 'baer-barger-800', 'baer-barger-1000',
  'seesaw-B0045', 'seesaw-C0893', 'seesaw-B0461', 'seesaw-B0581'].forEach((id) => { PAPER_HALO[id] = [LZF, 'LZ fixed Earth speed 254 km/s']; });
let MAP = null;
let last = null;

// ---------- formatting ----------
const fmtMass = (m) => (m >= 1000 ? `${(m / 1000).toFixed(m >= 10000 ? 0 : 2)} TeV` : `${m >= 100 ? m.toFixed(0) : m.toFixed(1)} GeV`);
const fmtDelta = (d) => `${d > 0 ? '+' : d < 0 ? '−' : ''}${Math.abs(d).toFixed(Math.abs(d) < 100 ? 1 : 0)} keV`;
function fmtSci(x, digits = 2) {
  if (!isFinite(x) || x <= 0) return '–';
  const e = Math.floor(Math.log10(x));
  const mnt = x / 10 ** e;
  const sup = String(e).replace('-', '⁻').replace(/\d/g, (d) => '⁰¹²³⁴⁵⁶⁷⁸⁹'[d]);
  return `${mnt.toFixed(digits)} × 10${sup}`;
}
const fmtNum = (x, d = 2) => (!isFinite(x) ? '–' : x >= 100 ? x.toFixed(0) : x >= 10 ? x.toFixed(1) : x.toFixed(d));
const pct = (p) => (p >= 0.995 ? '> 99%' : p < 0.001 ? '< 0.1%' : p < 0.1 ? `${(100 * p).toFixed(1)}%` : `${Math.round(100 * p)}%`);

// ---------- state <-> controls ----------
function haloFromState(time = state.time) {
  const base = { ...DEFAULT_HALO, rho: state.rho, vesc: state.vesc, v0: state.v0, vE: state.vE };
  if (time === 'avg') return { ...base, dvE: 14.9, phase: null };
  if (time === 'fixed') return { ...base, dvE: 0, phase: null };
  if (time === 'event') return { ...base, dvE: 14.9, phase: EVENT_PHASE };
  return { ...base, dvE: 14.9, phase: 0.5 };
}
const detFromState = () => ({ ...DEFAULT_DET, energyScale: state.escale, sideband: [350, state.sbHi] });
const modelFromState = () => ({ m: state.m, delta: state.delta, coupling: state.coupling, sigma_n: state.norm === 'sigma' ? state.sigma : 1e-40 });

function syncControls() {
  $('#bench').value = state.bench || 'custom';
  $('#mass').value = Math.log10(state.m);
  $('#mass-out').value = fmtMass(state.m);
  $('#delta').value = state.delta;
  $('#delta-out').value = fmtDelta(state.delta);
  $('#coupling').value = state.coupling;
  document.querySelectorAll('input[name=norm]').forEach((r) => { r.checked = r.value === state.norm; });
  $('#sigma-wrap').hidden = state.norm !== 'sigma';
  $('#sigma').value = Math.log10(state.sigma);
  $('#sigma-out').value = `${fmtSci(state.sigma)} cm²`;
  $('#rho').value = state.rho; $('#rho-out').value = `${state.rho.toFixed(2)} GeV/cm³`;
  const ph = PAPER_HALO[state.bench];
  $('#paper-halo').disabled = !ph;
  $('#paper-halo-note').textContent = ph ? `This paper's halo: ${ph[1]}.` : '';
  $('#vesc').value = state.vesc; $('#vesc-out').value = `${state.vesc} km/s`;
  $('#v0').value = state.v0; $('#v0-out').value = `${state.v0} km/s`;
  $('#vE').value = state.vE; $('#vE-out').value = `${state.vE.toFixed(1)} km/s`;
  $('#time').value = state.time;
  $('#escale').value = String(state.escale);
  $('#sb').value = String(state.sbHi);
  $('#logy').checked = state.logy;
  const b = BENCH.find((x) => x.id === state.bench);
  $('#claim').innerHTML = b
    ? `${escapeHtml(b.authors)}, <a href="https://arxiv.org/abs/${b.arxiv}" target="_blank" rel="noopener">arXiv:${b.arxiv}</a>. Claim: ${escapeHtml(b.claim)}.${b.note ? ` <span>${escapeHtml(b.note.charAt(0).toUpperCase() + b.note.slice(1))}.</span>` : ''}`
    : 'Custom point. Pick a benchmark to load a published explanation.';
}

function escapeHtml(s) {
  return String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

function loadBench(id) {
  const b = BENCH.find((x) => x.id === id);
  if (!b) { state.bench = null; return; }
  state.bench = id;
  state.m = b.m; state.delta = b.delta; state.coupling = b.coupling;
  if (b.sigma_n) state.sigma = b.sigma_n;
}

function setHaloPreset(name) {
  let h = name === 'lz' ? LZF : COMMON;
  if (name === 'paper' && PAPER_HALO[state.bench]) h = PAPER_HALO[state.bench][0];
  Object.assign(state, { rho: h.rho, v0: h.v0, vesc: h.vesc, vE: h.vE, time: h.time });
}

// ---------- URL ----------
function writeUrl() {
  const q = new URLSearchParams();
  if (state.bench) q.set('b', state.bench);
  q.set('m', +state.m.toPrecision(5)); q.set('d', +state.delta.toFixed(2)); q.set('c', state.coupling);
  if (state.norm === 'sigma') q.set('s', state.sigma.toExponential(3));
  if (state.rho !== 0.3) q.set('rho', state.rho);
  if (state.vesc !== 544) q.set('vesc', state.vesc);
  if (state.v0 !== 238) q.set('v0', state.v0);
  if (state.vE !== 250.2) q.set('vE', state.vE);
  if (state.time !== 'avg') q.set('t', state.time);
  if (state.escale !== 1) q.set('es', state.escale);
  if (state.sbHi !== 590) q.set('sb', state.sbHi);
  history.replaceState(null, '', `${location.pathname}?${q}`);
}
function readUrl() {
  const q = new URLSearchParams(location.search);
  if (![...q.keys()].length) return;
  if (q.get('b')) loadBench(q.get('b'));
  const num = (k) => (q.has(k) && isFinite(+q.get(k)) ? +q.get(k) : null);
  if (num('m')) state.m = clamp(num('m'), 10, 3162);
  if (num('d') !== null) state.delta = clamp(num('d'), -3000, 600);
  if (['A', 'Z', 'QW'].includes(q.get('c'))) state.coupling = q.get('c');
  if (num('s')) { state.norm = 'sigma'; state.sigma = num('s'); }
  if (num('rho')) state.rho = clamp(num('rho'), 0.2, 0.6);
  if (num('vesc')) state.vesc = clamp(num('vesc'), 480, 650);
  if (num('v0')) state.v0 = clamp(num('v0'), 200, 270);
  if (num('vE')) state.vE = clamp(num('vE'), 215, 270);
  if (['avg', 'fixed', 'event', 'dec'].includes(q.get('t'))) state.time = q.get('t');
  if (num('es')) state.escale = num('es');
  if (num('sb')) state.sbHi = num('sb') === 680 ? 680 : 590;
  // Was a benchmark changed?
  const b = BENCH.find((x) => x.id === state.bench);
  if (b && (Math.abs(b.m - state.m) > 1e-6 * b.m || Math.abs(b.delta - state.delta) > 1e-6)) state.bench = null;
}
const clamp = (x, a, b) => Math.min(b, Math.max(a, x));

// ---------- compute ----------
function compute() {
  const model = modelFromState();
  const halo = haloFromState();
  const det = detFromState();
  if (!kinematicallyAllowed(model, halo)) return { forbidden: true };
  const p = predict(model, halo, det, OPTS);
  if (!(p.N_roi > 0)) return { forbidden: true, p };
  const T = timingFactor(model, haloFromState('avg'), det, OPTS);
  return { p, T, model };
}

function render() {
  writeUrl();
  syncControls();
  let r;
  try { r = compute(); } catch (e) { console.error(e); $('#verdict').textContent = 'Computation failed for this point.'; return; }
  last = r;
  drawSpectrum(r);
  drawMap();
  fillReadouts(r);
}

function fillReadouts(r) {
  const b = BENCH.find((x) => x.id === state.bench);
  if (r.forbidden) {
    ['#r-count', '#r-sb', '#r-chi', '#r-time', '#r-peak'].forEach((s) => { $(s).textContent = '–'; });
    ['#r-sb-p', '#r-chi-sub', '#r-time-sub', '#r-low'].forEach((s) => { $(s).textContent = ''; });
    $('#verdict').textContent = state.delta > 0
      ? `No particle in this halo is fast enough to pay a ${fmtDelta(state.delta)} splitting at ${fmtMass(state.m)}, so LZ would see nothing. Lower the splitting, raise the mass or raise the escape speed.`
      : 'No recoils land in LZ\'s window for this point.';
    fillAudit(b);
    return;
  }
  const { p, T } = r;
  const R = p.ratio_sb;
  if (state.norm === 'sigma') {
    $('#k-count').textContent = 'Events LZ would have selected';
    $('#r-count').textContent = fmtNum(p.N_roi);
  } else {
    $('#k-count').textContent = 'Cross-section for one event';
    $('#r-count').textContent = `${fmtSci(1e-40 / p.N_roi, 1)} cm²`;
  }
  $('#r-sb').textContent = fmtNum(R);
  const nSB = state.norm === 'sigma' ? p.N_sb : R;
  $('#r-sb-p').textContent = `P(sideband empty) ${pct(Math.exp(-nSB))}${state.norm === 'sigma' ? ` at ${fmtNum(p.N_sb)} expected` : ''}`;
  $('#r-chi').textContent = fmtNum(p.dchi2);
  $('#r-chi-sub').textContent = `shape alone ${fmtNum(p.dchi2_roi)}; 0 = a perfect line at 248 keV`;
  $('#r-time').textContent = `× ${fmtNum(T)}`;
  const dT = -2 * Math.log(T);
  $('#r-time-sub').textContent = `${dT < 0 ? 'subtracts' : 'adds'} ${fmtNum(Math.abs(dT))} ${dT < 0 ? 'from' : 'to'} Δχ²`;
  $('#r-peak').textContent = `${Math.round(p.E_peak)} keV`;
  $('#r-low').textContent = `${pct(p.N_low / p.N_roi)} of events below 55 keV`;
  fillAudit(b);
  $('#verdict').textContent = verdict(p, T);
}

function fillAudit(b) {
  if (b && b.python && isFinite(b.python.R_SB)) {
    $('#r-audit').textContent = `${fmtNum(b.python.R_SB)} · ${fmtNum(b.python.dchi2)}`;
    $('#r-audit-sub').textContent = 'Sideband per event · Δχ² from the Python audit: common halo, year-averaged, nominal detector.';
  } else if (b) {
    $('#r-audit').textContent = '–';
    $('#r-audit-sub').textContent = 'No audit value: no recoils on the common halo.';
  } else {
    $('#r-audit').textContent = '–';
    $('#r-audit-sub').textContent = 'Load a benchmark to compare with the audit.';
  }
}

function verdict(p, T) {
  const parts = [];
  if (state.norm === 'sigma') {
    if (p.N_roi > 5) parts.push(`At this cross-section LZ should have selected about ${fmtNum(p.N_roi)} events, not one.`);
    else if (p.N_roi < 0.1) parts.push(`At this cross-section LZ would expect only ${fmtNum(p.N_roi)} events; one is a long shot.`);
    else parts.push(`At this cross-section LZ expects ${fmtNum(p.N_roi)} events, consistent with seeing one.`);
  }
  const R = p.ratio_sb;
  if (R < 0.3) parts.push('The empty sideband is no problem.');
  else if (R < 1) parts.push(`The empty sideband is a mild strain (${pct(Math.exp(-R))} chance it stays empty).`);
  else if (R < 3) parts.push(`The empty sideband is in tension: only a ${pct(Math.exp(-R))} chance it stays empty.`);
  else parts.push(`The empty sideband is a serious problem: ${pct(Math.exp(-R))} chance it stays empty, if LZ's sideband accepts these events.`);
  if (p.dchi2_roi < 1.2) parts.push('The spectrum is concentrated near 248 keV.');
  else if (p.dchi2_roi < 3) parts.push(`The event sits on the shoulder of a spectrum peaking at ${Math.round(p.E_peak)} keV.`);
  else parts.push(`The event sits in the tail of a spectrum peaking at ${Math.round(p.E_peak)} keV.`);
  if (T > 1.8) parts.push(`The June date helps: the rate then is ${fmtNum(T)} times the average.`);
  else if (T < 1.1) parts.push('The event date neither helps nor hurts.');
  return parts.join(' ');
}

// ---------- drawing ----------
function setupCanvas(cv) {
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const w = cv.clientWidth, h = cv.clientHeight;
  cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr);
  const c = cv.getContext('2d'); c.setTransform(dpr, 0, 0, dpr, 0, 0); c.clearRect(0, 0, w, h);
  return { c, w, h };
}

function drawSpectrum(r) {
  const cv = $('#spectrum');
  const { c, w, h } = setupCanvas(cv);
  const L = 62, Rm = 16, T = 18, B = 46, xmax = 800;
  const X = (x) => L + (x / xmax) * (w - L - Rm);
  c.font = '11px Arial'; c.lineWidth = 1;
  // Sideband
  c.fillStyle = 'rgba(208,106,106,0.16)';
  c.fillRect(X(350), T, X(state.sbHi) - X(350), h - T - B);
  c.fillStyle = COL.red; c.textAlign = 'center';
  c.fillText(X(800) - X(0) < 520 ? '0 seen' : 'sideband: LZ saw 0', (X(350) + X(state.sbHi)) / 2, T + 14);
  // Event band
  c.fillStyle = 'rgba(237,240,228,0.07)';
  c.fillRect(X(225), T, X(271) - X(225), h - T - B);
  if (r.forbidden || !r.p) {
    axesX(c, X, w, h, L, Rm, B, xmax);
    c.fillStyle = COL.muted; c.textAlign = 'center'; c.font = '14px Georgia';
    c.fillText('No recoils possible for this point', (L + w - Rm) / 2, h / 2);
    eventLine(c, X, T, h, B);
    return;
  }
  const { p } = r;
  const scale = state.norm === 'sigma' ? 1 : 1 / p.N_roi;
  const E = p.E, sel = p.selRec, all = p.allRec;
  let ymax = 0;
  for (let i = 0; i < E.length; i++) if (E[i] <= xmax) ymax = Math.max(ymax, sel[i] * scale, all[i] * scale);
  ymax = ymax > 0 ? ymax * 1.08 : 1;
  const ymin = state.logy ? ymax * 1e-4 : 0;
  const Y = state.logy
    ? (y) => h - B - (Math.log10(Math.max(y, ymin)) - Math.log10(ymin)) / (Math.log10(ymax) - Math.log10(ymin)) * (h - T - B)
    : (y) => h - B - (y / ymax) * (h - T - B);
  // Grid + y ticks
  c.strokeStyle = COL.line; c.fillStyle = COL.muted; c.textAlign = 'right';
  const ticks = state.logy ? [0, 1, 2, 3, 4].map((k) => ymax / 10 ** k) : [0, 0.25, 0.5, 0.75, 1].map((f) => f * ymax);
  ticks.forEach((y) => { c.beginPath(); c.moveTo(L, Y(y)); c.lineTo(w - Rm, Y(y)); c.stroke(); c.fillText(fmtTick(y), L - 6, Y(y) + 4); });
  axesX(c, X, w, h, L, Rm, B, xmax);
  c.save(); c.translate(14, (T + h - B) / 2); c.rotate(-Math.PI / 2); c.textAlign = 'center';
  c.fillText(state.norm === 'sigma' ? 'Events / keV' : 'Events / keV (per selected event)', 0, 0); c.restore();
  // Selected area
  const colr = state.delta >= 0 ? COL.mint : COL.peach;
  document.querySelector('.sw-sel').style.background = hexA(colr, 0.6);
  c.beginPath(); c.moveTo(X(0), Y(0));
  for (let i = 0; i < E.length && E[i] <= xmax; i++) c.lineTo(X(E[i]), Y(sel[i] * scale));
  c.lineTo(X(Math.min(E[E.length - 1], xmax)), Y(0)); c.closePath();
  c.fillStyle = hexA(colr, 0.45); c.fill();
  c.strokeStyle = colr; c.lineWidth = 1.5;
  c.beginPath();
  for (let i = 0; i < E.length && E[i] <= xmax; i++) (i ? c.lineTo : c.moveTo).call(c, X(E[i]), Y(sel[i] * scale));
  c.stroke();
  // All recoils, dotted
  c.setLineDash([2, 4]); c.strokeStyle = COL.ink; c.lineWidth = 1.2; c.beginPath();
  for (let i = 0; i < E.length && E[i] <= xmax; i++) (i ? c.lineTo : c.moveTo).call(c, X(E[i]), Y(all[i] * scale));
  c.stroke(); c.setLineDash([]);
  eventLine(c, X, T, h, B);
  cv.setAttribute('aria-label', `Recoil spectrum for ${fmtMass(state.m)}, splitting ${fmtDelta(state.delta)}: peak at ${Math.round(p.E_peak)} keV, ${fmtNum(p.ratio_sb)} sideband events per selected event.`);
}

function axesX(c, X, w, h, L, Rm, B, xmax) {
  c.strokeStyle = COL.line; c.fillStyle = COL.muted; c.textAlign = 'center'; c.font = '11px Arial';
  for (let x = 0; x <= xmax; x += 100) c.fillText(String(x), X(x), h - B + 18);
  c.fillText('Reconstructed recoil energy / keV', (L + w - Rm) / 2, h - 8);
}
function eventLine(c, X, T, h, B) {
  c.strokeStyle = COL.ink; c.lineWidth = 1.5; c.beginPath(); c.moveTo(X(248), T); c.lineTo(X(248), h - B); c.stroke();
  c.fillStyle = COL.ink; c.textAlign = 'right'; c.font = '11px Arial';
  c.fillText(X(800) - X(0) < 520 ? '248 keV' : 'the event, 248 keV', X(248) - 6, T + 14);
}
function fmtTick(y) {
  if (y === 0) return '0';
  if (y >= 0.001 && y < 1000) return y >= 1 ? y.toFixed(1) : String(+y.toPrecision(2));
  return y.toExponential(0);
}
function hexA(hex, a) {
  const n = parseInt(hex.slice(1), 16);
  return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`;
}

// Viridis (reversed: low penalty = bright)
const VIR = [[68, 1, 84], [72, 40, 120], [62, 74, 137], [49, 104, 142], [38, 130, 142], [31, 158, 137], [53, 183, 121], [109, 205, 89], [180, 222, 44], [253, 231, 37]];
function viridis(t) {
  t = clamp(t, 0, 1) * (VIR.length - 1);
  const i = Math.min(Math.floor(t), VIR.length - 2), f = t - i;
  return VIR[i].map((v, k) => Math.round(v + f * (VIR[i + 1][k] - v)));
}
const MAP_GEOM = { L: 62, R: 70, T: 16, B: 46 };

function drawMap() {
  if (!MAP) return;
  const cv = $('#map');
  const { c, w, h } = setupCanvas(cv);
  const { L, R, T, B } = MAP_GEOM;
  const lm0 = Math.log10(MAP.m[0]), lm1 = Math.log10(MAP.m[MAP.m.length - 1]);
  const d0 = MAP.delta[0], d1 = MAP.delta[MAP.delta.length - 1];
  const X = (m) => L + (Math.log10(m) - lm0) / (lm1 - lm0) * (w - L - R);
  const Y = (d) => h - B - (d - d0) / (d1 - d0) * (h - T - B);
  // Heatmap cells
  const nm = MAP.m.length, nd = MAP.delta.length;
  for (let i = 0; i < nd; i++) {
    for (let j = 0; j < nm; j++) {
      const v = MAP.dchi2[i][j];
      const xa = j === 0 ? X(MAP.m[0]) : (X(MAP.m[j - 1]) + X(MAP.m[j])) / 2;
      const xb = j === nm - 1 ? X(MAP.m[nm - 1]) : (X(MAP.m[j]) + X(MAP.m[j + 1])) / 2;
      const ya = i === nd - 1 ? Y(d1) : (Y(MAP.delta[i]) + Y(MAP.delta[i + 1])) / 2;
      const yb = i === 0 ? Y(d0) : (Y(MAP.delta[i - 1]) + Y(MAP.delta[i])) / 2;
      if (v === null) c.fillStyle = '#070b08';
      else { const [r, g, b2] = viridis(1 - Math.min(v, 12) / 12); c.fillStyle = `rgb(${r},${g},${b2})`; }
      c.fillRect(xa, ya, xb - xa + 0.6, yb - ya + 0.6);
    }
  }
  // Axes
  c.font = '11px Arial'; c.fillStyle = COL.muted; c.strokeStyle = 'rgba(237,240,228,0.25)';
  c.textAlign = 'center';
  [20, 50, 100, 200, 500, 1000, 2000].forEach((m) => { c.beginPath(); c.moveTo(X(m), T); c.lineTo(X(m), h - B); c.stroke(); c.fillText(m >= 1000 ? `${m / 1000} TeV` : `${m}`, X(m), h - B + 18); });
  c.fillText('Dark-matter mass / GeV', (L + w - R) / 2, h - 8);
  c.textAlign = 'right';
  for (let d = -3000; d <= 500; d += 500) { c.beginPath(); c.moveTo(L, Y(d)); c.lineTo(w - R, Y(d)); c.stroke(); c.fillText(String(d), L - 6, Y(d) + 4); }
  c.save(); c.translate(14, (T + h - B) / 2); c.rotate(-Math.PI / 2); c.textAlign = 'center'; c.fillText('Splitting δ / keV', 0, 0); c.restore();
  c.strokeStyle = COL.ink; c.lineWidth = 1; c.beginPath(); c.moveTo(L, Y(0)); c.lineTo(w - R, Y(0)); c.stroke();
  // Colour bar
  const cbx = w - R + 18, cbw = 12;
  for (let k = 0; k <= 100; k++) { const [r, g, b2] = viridis(1 - k / 100); c.fillStyle = `rgb(${r},${g},${b2})`; c.fillRect(cbx, Y(d0) - (k + 1) / 101 * (Y(d0) - Y(d1)), cbw, (Y(d0) - Y(d1)) / 101 + 1); }
  c.fillStyle = COL.muted; c.textAlign = 'left';
  [0, 4, 8, 12].forEach((v) => c.fillText(v === 12 ? '12+' : String(v), cbx + cbw + 4, Y(d0) - v / 12 * (Y(d0) - Y(d1)) + 4));
  c.textAlign = 'center'; c.fillText('Δχ²', cbx + cbw / 2, h - B + 18);
  // Benchmarks
  BENCH.forEach((b) => {
    if (b.m < MAP.m[0] || b.m > MAP.m[nm - 1]) return;
    c.beginPath(); c.arc(X(b.m), Y(b.delta), 4, 0, 2 * Math.PI);
    c.fillStyle = b.delta >= 0 ? COL.mint : COL.peach; c.fill(); c.strokeStyle = '#101914'; c.lineWidth = 1; c.stroke();
  });
  // Current point
  const cm = clamp(state.m, MAP.m[0], MAP.m[nm - 1]), cd = clamp(state.delta, d0, d1);
  c.beginPath(); c.arc(X(cm), Y(cd), 9, 0, 2 * Math.PI); c.strokeStyle = COL.ink; c.lineWidth = 2; c.stroke();
  cv._geom = { X, Y, lm0, lm1, d0, d1, w, h };
}

function mapClick(ev) {
  const cv = $('#map'); const g = cv._geom; if (!g) return;
  const rect = cv.getBoundingClientRect();
  const x = ev.clientX - rect.left, y = ev.clientY - rect.top;
  const { L, R, T, B } = MAP_GEOM;
  if (x < L || x > g.w - R || y < T || y > g.h - B) return;
  const lm = g.lm0 + (x - L) / (g.w - L - R) * (g.lm1 - g.lm0);
  const d = g.d0 + (g.h - B - y) / (g.h - T - B) * (g.d1 - g.d0);
  // Snap to a published benchmark if the click is close to one
  let snap = null, best = 10;
  BENCH.forEach((b) => { const dist = Math.hypot(g.X(b.m) - x, g.Y(b.delta) - y); if (dist < best) { best = dist; snap = b; } });
  if (snap) loadBench(snap.id);
  else { state.bench = null; state.m = 10 ** lm; state.delta = Math.round(d * 2) / 2; }
  schedule();
  document.getElementById('explorer').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ---------- wiring ----------
let pending = false;
function schedule() { if (pending) return; pending = true; requestAnimationFrame(() => { pending = false; render(); }); }

function wire() {
  $('#bench').addEventListener('change', (e) => { if (e.target.value === 'custom') state.bench = null; else loadBench(e.target.value); schedule(); });
  $('#mass').addEventListener('input', (e) => { state.m = 10 ** +e.target.value; state.bench = null; schedule(); });
  $('#delta').addEventListener('input', (e) => { state.delta = +e.target.value; state.bench = null; schedule(); });
  $('#coupling').addEventListener('change', (e) => { state.coupling = e.target.value; state.bench = null; schedule(); });
  document.querySelectorAll('input[name=norm]').forEach((r) => r.addEventListener('change', (e) => { state.norm = e.target.value; schedule(); }));
  $('#sigma').addEventListener('input', (e) => { state.sigma = 10 ** +e.target.value; schedule(); });
  $('#rho').addEventListener('input', (e) => { state.rho = +e.target.value; schedule(); });
  $('#vesc').addEventListener('input', (e) => { state.vesc = +e.target.value; schedule(); });
  $('#v0').addEventListener('input', (e) => { state.v0 = +e.target.value; schedule(); });
  $('#vE').addEventListener('input', (e) => { state.vE = +e.target.value; schedule(); });
  $('#time').addEventListener('change', (e) => { state.time = e.target.value; schedule(); });
  $('#escale').addEventListener('change', (e) => { state.escale = +e.target.value; schedule(); });
  $('#sb').addEventListener('change', (e) => { state.sbHi = +e.target.value; schedule(); });
  $('#logy').addEventListener('change', (e) => { state.logy = e.target.checked; schedule(); });
  document.querySelectorAll('[data-halo]').forEach((bt) => bt.addEventListener('click', () => { setHaloPreset(bt.dataset.halo); schedule(); }));
  document.querySelectorAll('[data-load]').forEach((bt) => bt.addEventListener('click', () => {
    loadBench(bt.dataset.load);
    if (bt.dataset.load === 'fan-reece') state.norm = 'sigma';
    schedule();
    document.getElementById('explorer').scrollIntoView({ behavior: 'smooth', block: 'start' });
  }));
  $('#controls').addEventListener('submit', (e) => e.preventDefault());
  $('#map').addEventListener('click', mapClick);
  let rt; window.addEventListener('resize', () => { clearTimeout(rt); rt = setTimeout(schedule, 120); });
}

function fillBenchSelect() {
  const sel = $('#bench');
  const groups = [['Endothermic (kicked up to a heavier state)', (b) => b.delta > 0], ['Exothermic (drops to a lighter state)', (b) => b.delta < 0]];
  sel.innerHTML = '<option value="custom">Custom point</option>';
  groups.forEach(([label, f]) => {
    const og = document.createElement('optgroup'); og.label = label;
    BENCH.filter(f).sort((a, b) => a.m - b.m || a.delta - b.delta).forEach((b) => {
      const o = document.createElement('option');
      o.value = b.id;
      o.textContent = `${b.authors.replace(/ \(.*\)$/, '')} · ${fmtMass(b.m)}, ${fmtDelta(b.delta)}`;
      og.appendChild(o);
    });
    sel.appendChild(og);
  });
}

async function main() {
  try {
    const [b, m] = await Promise.all([fetch('benchmarks.json').then((r) => r.json()), fetch('map.json').then((r) => r.json())]);
    BENCH = b; MAP = m;
  } catch (e) {
    console.error(e);
    $('#verdict').innerHTML = '<span class="error">Could not load the benchmark data. Serve this folder over HTTP rather than opening the file directly.</span>';
  }
  fillBenchSelect();
  loadBench(state.bench);
  readUrl();
  wire();
  render();
}

main();
