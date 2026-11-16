"""Build web/benchmarks.json from ../benchmarks.csv and ../results/benchmarks_common.csv.

Run: python build_benchmarks.py   (Python standard library only)
"""

import csv
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def num(v):
    if v in (None, "", "None"):
        return None
    x = float(v)
    return None if x != x else x


def main():
    with open(os.path.join(ROOT, "benchmarks.csv")) as f:
        bench = list(csv.DictReader(f))
    with open(os.path.join(ROOT, "results", "benchmarks_common.csv")) as f:
        res = {r["id"]: r for r in csv.DictReader(f)}
    out = []
    for b in bench:
        r = res.get(b["id"], {})
        out.append({
            "id": b["id"], "arxiv": b["arxiv"], "authors": b["authors"],
            "m": float(b["m_chi_GeV"]), "delta": float(b["delta_keV"]), "coupling": b["coupling"],
            "sigma_n": num(b["sigma_n_cm2"]), "claim": b["claim"], "paper_halo": b["paper_halo"], "note": b["note"],
            "python": {k: (r.get(k) if r.get(k) == "inf" else num(r.get(k)))
                       for k in ("R_SB", "dchi2", "timing_factor", "N_roi_own_sigma")},
        })
    with open(os.path.join(HERE, "benchmarks.json"), "w") as f:
        json.dump(out, f, indent=1)
    print(f"wrote {len(out)} benchmarks")


if __name__ == "__main__":
    main()
