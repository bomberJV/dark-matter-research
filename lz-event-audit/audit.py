"""Evaluate every published LZ 248 keV benchmark in one common framework.

Run: python audit.py
Writes results/ (CSV tables, JSON summary, figures).

Common framework (see rates.py):
  halo      SHM, rho 0.3, v0 238, vesc 544, vE 250.2 +/- 14.9 km/s year-averaged
  nucleus   natural xenon, Helm form factor
  detector  2.84 t yr; LZ efficiency (piecewise approximation of Fig. S2);
            resolution sqrt(23^2 E/248 + (0.093 E)^2) keV
  windows   ROI = efficiency-weighted 5.4-269.9 keV; low window 5.4-55 keV;
            sideband 350-590 keV reconstructed, unit acceptance (unpublished)

Metrics are normalisation-free unless a cross-section is given:
  R_SB    sideband events expected per ROI event
  f_low   share of ROI events in the 5.4-55 keV window
  dchi2   2 ln(ideal / model) for "one event at 248 keV, none elsewhere,
          empty sideband", cross-section profiled; 0 = a perfect line at 248 keV
"""

from __future__ import annotations

import csv
import json
import os
from dataclasses import replace

import numpy as np
from scipy.optimize import brentq, minimize_scalar

from rates import (Detector, Halo, Model, predict, delta_chi2, delta_chi2_roi_only,
                   M_N_GEV, vmin_kms, AMU_GEV)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results")
os.makedirs(OUT, exist_ok=True)

BASE_HALO = Halo(vE=250.2, dvE=14.9, label="SHM, year-averaged")
BASE_DET = Detector()

VARIANTS = {
    "base": (BASE_HALO, BASE_DET),
    "vesc500": (replace(BASE_HALO, vesc=500.0), BASE_DET),
    "vesc600": (replace(BASE_HALO, vesc=600.0), BASE_DET),
    "v0_220": (replace(BASE_HALO, v0=220.0), BASE_DET),
    "sb_350_680": (BASE_HALO, replace(BASE_DET, sideband=(350.0, 680.0))),
    "escale_-9.3%": (BASE_HALO, replace(BASE_DET, energy_scale=1 / 1.093)),
    "escale_+9.3%": (BASE_HALO, replace(BASE_DET, energy_scale=1.093)),
    "res_stat_only": (BASE_HALO, replace(BASE_DET, res_b=0.0)),
}

# Event time: 2023-06-16, i.e. 14 days after the June 2 peak of Earth's speed.
EVENT_PHASE = 14.0 / 365.25

# G_F^2 mu_n^2 / (2 pi) for m_chi >> m_n, in cm^2
G_F = 1.1663787e-5          # GeV^-2
GEV2_TO_CM2 = 0.3893794e-27
SIGMA_HIGGSINO_2PI = G_F ** 2 * M_N_GEV ** 2 / (2 * np.pi) * GEV2_TO_CM2
SIGMA_HIGGSINO_8PI = SIGMA_HIGGSINO_2PI / 4


def load_benchmarks():
    with open(os.path.join(HERE, "benchmarks.csv")) as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["m_chi_GeV"] = float(r["m_chi_GeV"])
        r["delta_keV"] = float(r["delta_keV"])
        r["sigma_n_cm2"] = float(r["sigma_n_cm2"]) if r["sigma_n_cm2"] else None
    return rows


def kinematic_ok(m, d, halo=BASE_HALO):
    """Can any recoil be produced? (endothermic needs delta < mu v_max^2 / 2)"""
    vmax = halo.vesc + halo.vE + halo.dvE
    mA = 131.29 * AMU_GEV
    mu = m * mA / (m + mA)
    return d < 0 or d < 0.5 * mu * (vmax / 299792.458) ** 2 * 1e6


def evaluate(row):
    m, d, c = row["m_chi_GeV"], row["delta_keV"], row["coupling"]
    out = {k: row[k] for k in ("id", "arxiv", "authors", "claim")}
    out.update(m_chi_GeV=m, delta_keV=d, coupling=c)
    if not kinematic_ok(m, d):
        out["status"] = "kinematically forbidden in common halo"
        return out
    mod = Model(m, d, c, row["sigma_n_cm2"])
    for name, (h, det) in VARIANTS.items():
        p = predict(mod, h, det)
        tag = "" if name == "base" else f"_{name}"
        out[f"R_SB{tag}"] = p.ratio_sb
        out[f"dchi2{tag}"] = delta_chi2(p, det)
        if name == "base":
            out["N_roi_own_sigma"] = p.N_roi if row["sigma_n_cm2"] else None
            out["f_low"] = p.N_low / p.N_roi if p.N_roi > 0 else None
            out["E_peak_keV"] = p.E_peak
            out["dchi2_roi_only"] = delta_chi2_roi_only(p, det)
            out["N_above_270_per_roi"] = p.N_above / p.N_roi if p.N_roi > 0 else None
    # Common-halo variant at fixed vE = 254 (the value several papers use)
    p254 = predict(mod, Halo(), BASE_DET)
    out["N_roi_own_sigma_vE254"] = p254.N_roi if row["sigma_n_cm2"] else None
    # Cross-section (paper's coupling convention) that gives one ROI event in the common halo
    p1 = predict(mod, BASE_HALO, BASE_DET, sigma_n=1e-40)
    out["sigma_one_event_cm2"] = 1e-40 / p1.N_roi if p1.N_roi > 0 else None
    # Timing: event-density on June 16 relative to the year average (ROI shape at 248 keV)
    pj = predict(mod, replace(BASE_HALO, phase=EVENT_PHASE), BASE_DET)
    out["timing_factor"] = pj.p_event / p1.p_event * (1e-40 / (mod.sigma_n or 1e-40)) if p1.p_event > 0 else None
    out["status"] = "ok"
    return out


def higgsino_conventions():
    """How much the factor-4 cross-section convention moves the higgsino fit."""
    rows = []
    for vesc in (544.0, 567.0, 610.0):
        h = replace(BASE_HALO, vesc=vesc)
        for m in (1000.0, 1100.0):
            for label, s in (("G_F^2 mu^2 / 2 pi", SIGMA_HIGGSINO_2PI), ("G_F^2 mu^2 / 8 pi", SIGMA_HIGGSINO_8PI)):
                f = lambda dd: predict(Model(m, dd, "QW", s), h, BASE_DET).N_roi - 1.0
                d1 = brentq(f, 200.0, 560.0, xtol=0.05)
                p = predict(Model(m, d1, "QW", s), h, BASE_DET)
                rows.append(dict(vesc_kms=vesc, m_chi_GeV=m, sigma_convention=label, sigma_n_cm2=s,
                                 delta_one_event_keV=d1, N_SB=p.N_sb, E_peak_keV=p.E_peak,
                                 dchi2=delta_chi2(p, BASE_DET), P_sideband_empty=float(np.exp(-p.N_sb))))
    return rows


def best_delta_for_mass(m, sign=+1):
    """Splitting that minimises dchi2 (ROI + sideband) at fixed mass."""
    if sign > 0:
        mA = 131.29 * AMU_GEV
        mu = m * mA / (m + mA)
        dmax = 0.5 * mu * ((BASE_HALO.vesc + BASE_HALO.vE + BASE_HALO.dvE) / 299792.458) ** 2 * 1e6
        lo, hi = 0.0, dmax - 0.5
    else:
        lo, hi = -6000.0, 0.0
    ds = np.linspace(lo, hi, 60)
    vals = [delta_chi2(predict(Model(m, dd, "A"), BASE_HALO, BASE_DET)) for dd in ds]
    i = int(np.nanargmin(vals))
    a, b = ds[max(i - 1, 0)], ds[min(i + 1, len(ds) - 1)]
    res = minimize_scalar(lambda dd: delta_chi2(predict(Model(m, dd, "A"), BASE_HALO, BASE_DET)),
                          bounds=(a, b), method="bounded", options={"xatol": 0.2})
    p = predict(Model(m, res.x, "A"), BASE_HALO, BASE_DET)
    return dict(m_chi_GeV=m, sign="endo" if sign > 0 else "exo", best_delta_keV=float(res.x),
                dchi2=float(res.fun), R_SB=p.ratio_sb, E_peak_keV=p.E_peak)


def scan_map(ms, ds):
    Z = np.full((len(ds), len(ms)), np.nan)
    for j, m in enumerate(ms):
        for i, dd in enumerate(ds):
            if not kinematic_ok(m, dd):
                continue
            p = predict(Model(m, dd, "A"), BASE_HALO, BASE_DET, n=1200)
            if p.N_roi > 0:
                Z[i, j] = delta_chi2(p)
    return Z


def write_csv(path, rows):
    keys = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({k: (f"{v:.4g}" if isinstance(v, float) else v) for k, v in r.items()})


def main():
    bench = load_benchmarks()
    results = [evaluate(r) for r in bench]
    write_csv(os.path.join(OUT, "benchmarks_common.csv"), results)

    conv = higgsino_conventions()
    write_csv(os.path.join(OUT, "higgsino_conventions.csv"), conv)

    masses = [30, 42, 50, 70, 100, 200, 300, 500, 700, 1000, 1500, 2000, 3000]
    best = []
    for m in masses:
        if m >= 200:
            best.append(best_delta_for_mass(m, +1))
        best.append(best_delta_for_mass(m, -1))
    write_csv(os.path.join(OUT, "best_delta_by_mass.csv"), best)

    ms = np.geomspace(20, 3000, 40)
    ds = np.linspace(-3000, 520, 90)
    Z = scan_map(ms, ds)
    np.savez(os.path.join(OUT, "dchi2_map.npz"), m=ms, delta=ds, dchi2=Z)

    summary = dict(framework=dict(halo=BASE_HALO.__dict__, detector={k: v for k, v in BASE_DET.__dict__.items()}),
                   sigma_higgsino_2pi=SIGMA_HIGGSINO_2PI, sigma_higgsino_8pi=SIGMA_HIGGSINO_8PI,
                   n_benchmarks=len(results))
    with open(os.path.join(OUT, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
