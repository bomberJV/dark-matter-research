"""Figures for the LZ 248 keV audit. Run after audit.py."""

import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from rates import Model, predict
from audit import BASE_HALO, BASE_DET, kinematic_ok

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results")

plt.rcParams.update({'figure.facecolor': '#101914', 'axes.facecolor': '#101914', 'savefig.facecolor': '#101914',
                     'text.color': '#edf0e4', 'axes.labelcolor': '#d1d8ca', 'xtick.color': '#a5b8aa',
                     'ytick.color': '#a5b8aa', 'axes.edgecolor': '#526258', 'font.size': 11, 'axes.grid': True,
                     'grid.color': '#33443a', 'grid.alpha': .55, 'font.family': 'DejaVu Sans', 'svg.fonttype': 'none'})
ENDO, EXO, CRIT = '#66d9cb', '#ffb784', '#edf0e4'


def savefig(fig, name):
    fig.savefig(os.path.join(OUT, f"{name}.svg"), bbox_inches="tight")
    fig.savefig(os.path.join(OUT, f"{name}.png"), dpi=160, bbox_inches="tight")
    plt.close(fig)


def load(name):
    with open(os.path.join(OUT, name)) as f:
        return list(csv.DictReader(f))


def fig_map():
    d = np.load(os.path.join(OUT, "dchi2_map.npz"))
    ms, ds, Z = d["m"], d["delta"], d["dchi2"]
    fig, ax = plt.subplots(figsize=(8.6, 5.6))
    levels = [0, 1, 2, 3, 4, 6, 9, 16]
    cs = ax.contourf(ms, ds, np.clip(Z, 0, 16), levels=levels, cmap="viridis_r", alpha=.9)
    cb = fig.colorbar(cs, ax=ax)
    cb.set_label("Δχ² vs. an ideal line at 248 keV\n(one ROI event, empty sideband; σ profiled)")
    ax.axhline(0, color='#a5b8aa', lw=.8)
    rows = load("benchmarks_common.csv")
    for r in rows:
        m, dd = float(r["m_chi_GeV"]), float(r["delta_keV"])
        col = EXO if dd < 0 else ENDO
        ax.scatter(m, dd, s=36, color=col, edgecolor='#101914', zorder=5)
    ax.set_xscale("log")
    ax.set(xlabel="Dark-matter mass / GeV", ylabel="Splitting δ / keV  (δ < 0: exothermic)",
           title="Every published benchmark on one map (common halo, LZ response)")
    ax.text(25, 380, "endothermic:\nno recoils possible", fontsize=8, color='#a5b8aa', va="bottom")
    ax.scatter([], [], color=ENDO, label="endothermic benchmark")
    ax.scatter([], [], color=EXO, label="exothermic benchmark")
    ax.legend(fontsize=8, loc="lower right")
    savefig(fig, "benchmark-map")


def fig_spectra():
    picks = [("Higgsino tuned to 1 event\n1.1 TeV, δ 377 keV (Rodd et al.)", Model(1100, 377, "QW")),
             ("Pseudo-Dirac, relic σ\n1 TeV, δ 297 keV (Di Mauro)", Model(1000, 297.05, "A")),
             ("Exothermic, heavy\n500 GeV, δ −350 keV (Baer & Barger)", Model(500, -350, "Z")),
             ("Exothermic, light\n50 GeV, δ −1000 keV (2609.26570)", Model(50, -1000, "Z"))]
    fig, axs = plt.subplots(2, 2, figsize=(10, 6.6), sharex=True)
    for ax, (title, mod) in zip(axs.flat, picks):
        p = predict(mod, BASE_HALO, BASE_DET)
        E = p.grid["Erec"]
        norm_ = 1.0 / p.N_roi
        ax.fill_between(E, p.grid["sel_rec"] * norm_, color=ENDO if mod.delta > 0 else EXO, alpha=.45,
                        label="selected (ROI efficiency)")
        ax.plot(E, p.grid["all_rec"] * norm_, color=CRIT, lw=1, ls=":", label="all recoils")
        ax.axvspan(*BASE_DET.sideband, color='#c06060', alpha=.18, label="high-energy sideband")
        ax.axvline(248, color=CRIT, lw=1.2)
        ax.set_title(title, fontsize=10)
        ax.text(0.98, 0.92, f"sideband: {p.ratio_sb:.2f} per ROI event", transform=ax.transAxes,
                ha="right", fontsize=9)
        ax.set_xlim(0, 800)
        ax.set_ylim(bottom=0)
    for ax in axs[1]:
        ax.set_xlabel("Reconstructed recoil energy / keV")
    for ax in axs[:, 0]:
        ax.set_ylabel("Events / keV\n(scaled to one ROI event)")
    axs[0, 0].legend(fontsize=7.5, loc="upper left")
    fig.tight_layout()
    savefig(fig, "benchmark-spectra")


def fig_robustness():
    rows = [r for r in load("benchmarks_common.csv") if r["status"] == "ok"]
    variants = [("R_SB", "baseline", 'o'), ("R_SB_vesc500", "vesc 500", 'v'), ("R_SB_vesc600", "vesc 600", '^'),
                ("R_SB_escale_-9.3%", "energy scale −9.3%", '<'), ("R_SB_escale_+9.3%", "energy scale +9.3%", '>')]
    rows.sort(key=lambda r: float(r["R_SB"]))
    fig, ax = plt.subplots(figsize=(8.6, 7.4))
    y = np.arange(len(rows))
    for key, lab, mk in variants:
        vals = []
        for r in rows:
            v = r.get(key, "")
            v = float(v) if v not in ("", "inf") else np.nan
            vals.append(v)
        ax.scatter(vals, y, marker=mk, s=28 if key == "R_SB" else 18, label=lab,
                   color=CRIT if key == "R_SB" else None, zorder=4 if key == "R_SB" else 3)
    ax.set_yticks(y)
    ax.set_yticklabels([f"{r['id']}  ({float(r['m_chi_GeV']):.0f} GeV, {float(r['delta_keV']):.0f} keV)" for r in rows],
                       fontsize=8)
    ax.set_xscale("log")
    ax.axvline(1, color='#c06060', lw=1)
    ax.axvline(3, color='#c06060', lw=1, ls=":")
    ax.set(xlabel="Sideband events expected per ROI event", title="Sideband expectation and how far it moves")
    ax.text(0.95, len(rows) - 0.4, "P(empty) 37% ", fontsize=8, color='#c06060', ha="right")
    ax.text(3.15, len(rows) - 0.4, "5%", fontsize=8, color='#c06060')
    ax.legend(fontsize=8, loc="lower right")
    fig.tight_layout()
    savefig(fig, "sideband-robustness")


if __name__ == "__main__":
    fig_map()
    fig_spectra()
    fig_robustness()
    print("figures written")
