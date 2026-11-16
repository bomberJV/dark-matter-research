"""Turn the audit CSVs into the Markdown tables used in README.md. Run after audit.py."""

import csv
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results")


def f(x, nd=2, sci=False):
    if x in (None, "", "None"):
        return "–"
    v = float(x)
    if math.isinf(v):
        return "no ROI events"
    if sci:
        return f"{v:.1e}"
    return f"{v:.{nd}f}"


def main():
    rows = list(csv.DictReader(open(os.path.join(OUT, "benchmarks_common.csv"))))
    for r in rows:
        t = r.get("timing_factor")
        r["_combined"] = float(r["dchi2"]) - 2 * math.log(float(t)) if t not in (None, "") else None
    rows.sort(key=lambda r: r["_combined"])
    lines = ["| Benchmark | arXiv | m (GeV) | δ (keV) | Sideband per ROI event | range over halo & energy-scale variants "
             "| Δχ² shape + sideband | June-16 rate factor | Δχ² incl. timing | ROI events with paper's σ (common halo) |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    keys = ["R_SB", "R_SB_vesc500", "R_SB_vesc600", "R_SB_escale_-9.3%", "R_SB_escale_+9.3%", "R_SB_v0_220"]
    for r in rows:
        vals = [float(r[k]) for k in keys if r.get(k) not in (None, "", "inf")]
        rng = f"{min(vals):.2f}–{max(vals):.2f}"
        if any(r.get(k) == "inf" for k in keys):
            rng += " (no ROI events at vesc 500)"
        lines.append(f"| {r['id']} | {r['arxiv']} | {float(r['m_chi_GeV']):g} | {float(r['delta_keV']):g} | "
                     f"{f(r['R_SB'])} | {rng} | {f(r['dchi2'])} | {f(r['timing_factor'])} | {r['_combined']:.2f} | "
                     f"{f(r.get('N_roi_own_sigma'), 2)} |")
    open(os.path.join(OUT, "table_benchmarks.md"), "w").write("\n".join(lines) + "\n")

    conv = list(csv.DictReader(open(os.path.join(OUT, "higgsino_conventions.csv"))))
    lines = ["| vesc (km/s) | m (GeV) | σ convention | σ_n (cm²) | δ for one ROI event (keV) | sideband events | P(sideband empty) |",
             "|---|---|---|---|---|---|---|"]
    for r in conv:
        lines.append(f"| {float(r['vesc_kms']):g} | {float(r['m_chi_GeV']):g} | {r['sigma_convention']} | "
                     f"{float(r['sigma_n_cm2']):.2e} | {float(r['delta_one_event_keV']):.1f} | {float(r['N_SB']):.2f} | "
                     f"{100*float(r['P_sideband_empty']):.1f}% |")
    open(os.path.join(OUT, "table_higgsino.md"), "w").write("\n".join(lines) + "\n")

    best = list(csv.DictReader(open(os.path.join(OUT, "best_delta_by_mass.csv"))))
    lines = ["| m (GeV) | branch | best δ (keV) | Δχ² | sideband per ROI event | spectrum peak (keV) |",
             "|---|---|---|---|---|---|"]
    for r in best:
        lines.append(f"| {float(r['m_chi_GeV']):g} | {r['sign']} | {float(r['best_delta_keV']):.0f} | {float(r['dchi2']):.2f} | "
                     f"{float(r['R_SB']):.2g} | {float(r['E_peak_keV']):.0f} |")
    open(os.path.join(OUT, "table_best_delta.md"), "w").write("\n".join(lines) + "\n")
    print(open(os.path.join(OUT, "table_benchmarks.md")).read())
    print(open(os.path.join(OUT, "table_higgsino.md")).read())


if __name__ == "__main__":
    main()
