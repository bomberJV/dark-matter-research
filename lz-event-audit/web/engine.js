// Nuclear-recoil rates in xenon for elastic and inelastic dark matter.
// A line-by-line port of ../rates.py (same constants, isotopes, form factor,
// halo, detector model and likelihood) for the browser and Node.
//
// Conventions: energies in keV, speeds in km/s, cross-sections in cm^2,
// masses in GeV. delta > 0 endothermic, delta < 0 exothermic.

const C_KMS = 299792.458;
const AMU_GEV = 0.93149410242;
const M_P_GEV = 0.93827208816;
const M_N_GEV = 0.93956542052;
const HBARC_GEV_FM = 0.1973269804;
const GEV_TO_KG = 1.78266192e-27;
const KEV_TO_J = 1.602176634e-16;
const SIN2_THETA_W = 0.2312;
const SECONDS_PER_YEAR = 365.25 * 86400.0;
const KG_PER_TONNE = 1000.0;
const SQRT_PI = Math.sqrt(Math.PI);
const SQRT_2PI = Math.sqrt(2 * Math.PI);

// Natural xenon: [A, Z, mole fraction, atomic mass in u]
export const XENON = [
  [124, 54, 0.000952, 123.905893],
  [126, 54, 0.000890, 125.904274],
  [128, 54, 0.019102, 127.903531],
  [129, 54, 0.264006, 128.904779],
  [130, 54, 0.040710, 129.903508],
  [131, 54, 0.212324, 130.905082],
  [132, 54, 0.269086, 131.904154],
  [134, 54, 0.104357, 133.905395],
  [136, 54, 0.088573, 135.907219],
];

export const DEFAULT_HALO = { rho: 0.3, v0: 238, vesc: 544, vE: 250.2, dvE: 14.9, phase: null };
export const LZ_HALO_FIXED = { rho: 0.3, v0: 238, vesc: 544, vE: 254, dvE: 0, phase: null };
export const DEFAULT_DET = {
  exposure: 2.84, effE: [5.4, 14, 250, 269.9], effV: [0.5, 0.96, 0.96, 0.5], effFloorE: 4, effCeilE: 285,
  resA: 23, resB: 0.093, sideband: [350, 590], lowWindow: [5.4, 55], eventE: 248, energyScale: 1,
};
export const EVENT_PHASE = 14 / 365.25;

// --- Special functions -------------------------------------------------------

// Complementary error function, Chebyshev fit (Numerical Recipes 3rd ed., 6.2),
// relative accuracy about 1e-16.
const ERFC_COF = [-1.3026537197817094, 6.4196979235649026e-1,
  1.9476473204185836e-2, -9.561514786808631e-3, -9.46595344482036e-4,
  3.66839497852761e-4, 4.2523324806907e-5, -2.0278578112534e-5,
  -1.624290004647e-6, 1.303655835580e-6, 1.5626441722e-8, -8.5238095915e-8,
  6.529054439e-9, 5.059343495e-9, -9.91364156e-10, -2.27365122e-10,
  9.6467911e-11, 2.394038e-12, -6.886027e-12, 8.94487e-13, 3.13092e-13,
  -1.12708e-13, 3.81e-16, 7.106e-15, -1.523e-15, -9.4e-17, 1.21e-16, -2.8e-17];

function erfccheb(z) {
  const t = 2 / (2 + z), ty = 4 * t - 2;
  let d = 0, dd = 0;
  for (let j = ERFC_COF.length - 1; j > 0; j--) {
    const tmp = d;
    d = ty * d - dd + ERFC_COF[j];
    dd = tmp;
  }
  return t * Math.exp(-z * z + 0.5 * (ERFC_COF[0] + ty * d) - dd);
}

export function erfc(x) { return x >= 0 ? erfccheb(x) : 2 - erfccheb(-x); }
export function erf(x) { return x >= 0 ? 1 - erfccheb(x) : erfccheb(-x) - 1; }
export function normCdf(x) { return 0.5 * erfc(-x / Math.SQRT2); }

function j1(x) {
  if (Math.abs(x) < 1e-3) { const x2 = x * x; return x / 3 * (1 - x2 / 10 + x2 * x2 / 280); }
  return Math.sin(x) / (x * x) - Math.cos(x) / x;
}

// --- Nuclear physics -------------------------------------------------------

function helmFF2(EkeV, A, mA) {
  const q = Math.sqrt(2 * mA * EkeV * 1e-6) / HBARC_GEV_FM;   // fm^-1
  const s = 0.9, a = 0.52;
  const c = 1.23 * Math.cbrt(A) - 0.60;
  const rn = Math.sqrt(c * c + (7 / 3) * Math.PI * Math.PI * a * a - 5 * s * s);
  const qr = Math.max(q * rn, 1e-9);
  const F = 3 * j1(qr) / qr * Math.exp(-(q * s) * (q * s) / 2);
  return F * F;
}

function couplingWeight(coupling, A, Z) {
  const N = A - Z;
  switch (coupling) {
    case 'A': return A * A;
    case 'Z': return Z * Z;
    case 'N': return N * N;
    case 'QW': { const q = N - (1 - 4 * SIN2_THETA_W) * Z; return q * q; }
    default: throw new Error(`unknown coupling ${coupling}`);
  }
}

function referenceNucleonMass(coupling) {
  if (coupling === 'Z') return M_P_GEV;
  if (coupling === 'N' || coupling === 'QW') return M_N_GEV;
  return AMU_GEV;
}

// --- Halo ------------------------------------------------------------------

// Mean inverse speed (s/km), truncated Maxwellian in the lab frame.
// Uses erfc differences, algebraically identical to the erf form in rates.py.
// Halo-dependent constants are precomputed once per Earth speed.
function etaConsts(v0, vesc, vE) {
  const y = vE / v0, z = vesc / v0;
  const Nesc = erf(z) - 2 * z / SQRT_PI * Math.exp(-z * z);
  return { v0, y, z, pref: 1 / (2 * Nesc * v0 * y), ez: Math.exp(-z * z), erfcz: erfc(z) };
}

function etaFast(vmin, c) {
  const x = vmin / c.v0, y = c.y, z = c.z;
  let out;
  if (x < z - y) out = c.pref * (erfc(x - y) - erfc(x + y) - 4 * y / SQRT_PI * c.ez);
  else if (x < z + y) out = c.pref * (erfc(x - y) - c.erfcz - 2 * (z + y - x) / SQRT_PI * c.ez);
  else out = 0;
  return out > 0 ? out : 0;
}

function vEarthSamples(halo, nTime) {
  if (!halo.dvE) return [halo.vE];
  if (halo.phase !== null && halo.phase !== undefined) return [halo.vE + halo.dvE * Math.cos(2 * Math.PI * halo.phase)];
  const out = new Array(nTime);
  for (let k = 0; k < nTime; k++) out[k] = halo.vE + halo.dvE * Math.cos(2 * Math.PI * (k + 0.5) / nTime);
  return out;
}

export function vminKms(E, m, delta, mA) {
  const Eg = E * 1e-6, d = delta * 1e-6;
  const mu = m * mA / (m + mA);
  return Math.abs(mA * Eg / mu + d) / Math.sqrt(2 * mA * Eg) * C_KMS;
}

// --- Detector --------------------------------------------------------------

function interp(x, xs, ys) {
  if (x <= xs[0]) return ys[0];
  const n = xs.length;
  if (x >= xs[n - 1]) return ys[n - 1];
  for (let i = 1; i < n; i++) {
    if (x <= xs[i]) { const t = (x - xs[i - 1]) / (xs[i] - xs[i - 1]); return ys[i - 1] + t * (ys[i] - ys[i - 1]); }
  }
  return ys[n - 1];
}

const clip01 = (v) => (v < 0 ? 0 : v > 1 ? 1 : v);

export function efficiency(E, det = DEFAULT_DET) {
  const xs = det.effE, ys = det.effV;
  const loE = xs[0], hiE = xs[xs.length - 1], loV = ys[0], hiV = ys[ys.length - 1];
  if (E < loE) return loV * clip01((E - det.effFloorE) / (loE - det.effFloorE));
  if (E > hiE) return hiV * clip01((det.effCeilE - E) / (det.effCeilE - hiE));
  return interp(E, xs, ys);
}

export function sigmaE(E, det = DEFAULT_DET) {
  return Math.sqrt(det.resA * det.resA * E / 248 + (det.resB * E) * (det.resB * E));
}

// --- Rates -----------------------------------------------------------------

function grid(n, Emax) {
  const E = new Float64Array(n);
  const step = (Emax - 0.5) / (n - 1);
  for (let i = 0; i < n; i++) E[i] = 0.5 + i * step;
  return E;
}

// Differential rate, events / (tonne yr keV), true recoil energy, on grid E.
export function dRdE(E, model, halo = DEFAULT_HALO, opts = {}) {
  const nTime = opts.nTime ?? 24;
  const sN = opts.sigma_n ?? model.sigma_n ?? 1e-40;
  const coupling = model.coupling ?? 'A';
  const qPower = model.q_power ?? 0;
  const n = E.length;
  const mRef = referenceNucleonMass(coupling);
  const muRef = model.m * mRef / (model.m + mRef);
  const masses = XENON.map((iso) => iso[3] * AMU_GEV);
  let norm = 0;
  for (let i = 0; i < XENON.length; i++) norm += XENON[i][2] * masses[i];
  const rhoKgM3 = halo.rho * GEV_TO_KG * 1e6;
  const consts = vEarthSamples(halo, nTime).map((vE) => etaConsts(halo.v0, halo.vesc, vE));
  const vCut = Math.max(...consts.map((c) => (c.z + c.y) * c.v0));
  const total = new Float64Array(n);
  for (let k = 0; k < XENON.length; k++) {
    const [A, Z, frac] = XENON[k];
    const mA = masses[k];
    const w = frac * mA / norm;
    const muA = model.m * mA / (model.m + mA);
    const sigmaA = sN * (muA / muRef) ** 2 * couplingWeight(coupling, A, Z);
    const pref = rhoKgM3 * sigmaA * 1e-4 / (2 * model.m * GEV_TO_KG * (muA * GEV_TO_KG) ** 2);
    for (let i = 0; i < n; i++) {
      let F2 = helmFF2(E[i], A, mA);
      if (qPower) F2 *= ((2 * mA * E[i] * 1e-6) / 0.01) ** qPower;
      if (F2 === 0) continue;
      const vmin = vminKms(E[i], model.m, model.delta, mA);
      if (vmin >= vCut) continue;
      let et = 0;
      for (let t = 0; t < consts.length; t++) et += etaFast(vmin, consts[t]);
      et = (et / consts.length) * 1e-3;       // s/m
      total[i] += w * pref * F2 * et;
    }
  }
  const conv = KEV_TO_J * KG_PER_TONNE * SECONDS_PER_YEAR;
  for (let i = 0; i < n; i++) total[i] *= conv;
  return total;
}

const KERNELS = new Map();

function kernel(det, n, Emax) {
  const key = `${det.resA}|${det.resB}|${det.energyScale}|${n}|${Emax}`;
  let K = KERNELS.get(key);
  if (K) return K;
  const E = grid(n, Emax);
  const k = det.energyScale;
  K = new Float64Array(n * n);
  for (let j = 0; j < n; j++) {
    const s = k * sigmaE(E[j], det), mu = k * E[j];
    const c = 1 / (s * SQRT_2PI);
    for (let i = 0; i < n; i++) { const u = (E[i] - mu) / s; K[i * n + j] = c * Math.exp(-0.5 * u * u); }
  }
  if (KERNELS.size > 8) KERNELS.delete(KERNELS.keys().next().value);
  KERNELS.set(key, K);
  return K;
}

export function predict(model, halo = DEFAULT_HALO, det = DEFAULT_DET, opts = {}) {
  const n = opts.n ?? 1200, Emax = opts.Emax ?? 1200;
  const E = grid(n, Emax);
  const dE = E[1] - E[0];
  const r = dRdE(E, model, halo, opts);
  const allTrue = new Float64Array(n), selTrue = new Float64Array(n);
  for (let i = 0; i < n; i++) { allTrue[i] = r[i] * det.exposure; selTrue[i] = allTrue[i] * efficiency(E[i], det); }
  const K = kernel(det, n, Emax);
  const selRec = new Float64Array(n), allRec = new Float64Array(n);
  for (let i = 0; i < n; i++) {
    let a = 0, b = 0;
    const row = i * n;
    for (let j = 0; j < n; j++) { const kk = K[row + j]; a += kk * selTrue[j]; b += kk * allTrue[j]; }
    selRec[i] = a * dE; allRec[i] = b * dE;
  }
  const k = det.energyScale;
  const [lo, hi] = det.lowWindow, [sa, sb] = det.sideband;
  let N_roi = 0, N_low = 0, N_sb = 0, N_above = 0;
  for (let i = 0; i < n; i++) {
    N_roi += selTrue[i];
    if (E[i] >= lo && E[i] <= hi) N_low += selTrue[i];
    if (E[i] > 270) N_above += allTrue[i];
    if (allTrue[i] > 0) {
      const s = k * sigmaE(E[i], det);
      N_sb += allTrue[i] * (normCdf((sb - k * E[i]) / s) - normCdf((sa - k * E[i]) / s));
    }
  }
  N_roi *= dE; N_low *= dE; N_sb *= dE; N_above *= dE;
  let iPeak = 0, tot = 0, below = 0;
  for (let i = 0; i < n; i++) {
    if (selRec[i] > selRec[iPeak]) iPeak = i;
    tot += selRec[i];
    if (E[i] < 150) below += selRec[i];
  }
  const p_event = interp(det.eventE, E, selRec);
  const ratio_sb = N_roi > 0 ? N_sb / N_roi : Infinity;
  const ref = 1 / (SQRT_2PI * sigmaE(det.eventE, det) * det.energyScale);
  const sc = N_roi + N_sb > 0 ? p_event / (N_roi + N_sb) : 0;
  const scRoi = N_roi > 0 ? p_event / N_roi : 0;
  return {
    E, selTrue, allTrue, selRec, allRec,
    N_roi, N_low, N_sb, N_above, p_event,
    E_peak: E[iPeak], frac150: below / Math.max(tot, 1e-300), ratio_sb,
    dchi2: sc > 0 ? 2 * Math.log(ref / sc) : Infinity,
    dchi2_roi: scRoi > 0 ? 2 * Math.log(ref / scRoi) : Infinity,
  };
}

export function sigmaForOneEvent(model, halo = DEFAULT_HALO, det = DEFAULT_DET, opts = {}) {
  const p = predict(model, halo, det, { ...opts, sigma_n: 1e-40 });
  return p.N_roi > 0 ? 1e-40 / p.N_roi : Infinity;
}

export function timingFactor(model, halo = DEFAULT_HALO, det = DEFAULT_DET, opts = {}) {
  const avg = predict(model, halo, det, { ...opts, sigma_n: 1e-40 });
  const june = predict(model, { ...halo, phase: EVENT_PHASE }, det, { ...opts, sigma_n: 1e-40 });
  return avg.p_event > 0 ? june.p_event / avg.p_event : null;
}

export function kinematicallyAllowed(model, halo = DEFAULT_HALO) {
  const vmax = halo.vesc + halo.vE + (halo.dvE || 0);
  const mA = 131.29 * AMU_GEV;
  const mu = model.m * mA / (model.m + mA);
  return model.delta < 0 || model.delta < 0.5 * mu * (vmax / C_KMS) ** 2 * 1e6;
}

export function deltaForOneEvent(model, halo = DEFAULT_HALO, det = DEFAULT_DET, opts = {}) {
  const f = (d) => predict({ ...model, delta: d }, halo, det, opts).N_roi - 1;
  let a = opts.lo ?? 200, b = opts.hi ?? 560;
  let fa = f(a), fb = f(b);
  if (!(fa > 0 && fb < 0) && !(fa < 0 && fb > 0)) return null;
  while (b - a > (opts.xtol ?? 0.05)) {
    const c = 0.5 * (a + b), fc = f(c);
    if ((fc > 0) === (fa > 0)) { a = c; fa = fc; } else { b = c; fb = fc; }
  }
  return 0.5 * (a + b);
}
