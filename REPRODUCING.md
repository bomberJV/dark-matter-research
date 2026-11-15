# Dark Matter, by Its Consequences

AI-assisted working paper prepared for Brandon Frank Han-Chween Huang, November 13, 2026. Not peer-reviewed.

## Reproduce numerical results

Use Python 3.11+ and the versions in requirements.txt (Python 3.12.14 was used here). Install into your own environment, then run `python3 analyze.py`. No network is required: the exact public SPARC source files are included with SHA-256 checksums in results/summary.json. The run performs analytic-integral and noiseless-recovery checks before fitting. Runtime is a few minutes on a typical CPU.

## Outputs

- results/profile_fits.csv: 100 selected galaxies × 4 configurations (disc M/L 0.3, 0.5, 0.7 with 5 km/s floor; M/L 0.5 with zero floor).
- results/sample_selection.csv: selection decision for all 175 parent galaxies.
- results/synthetic_trials.csv: 100 realizations × 2 generating profiles × 3 radius cuts.
- results/fits.json: baseline halo parameters, χ², optimizer and boundary flags.
- results/summary.json: analysis summary, software versions, seed and input hashes.
- results/curves.json: the four illustrative galaxies and their baseline fits.
- SVG/PNG figures: generated directly from these computations.

The web edition contains an interactive viewer of precomputed fits. It does not refit in the browser. Serve `web/` with `python3 -m http.server 8000 --directory web` to read it locally; the notebook navigation links lead to the original hosted site in the standalone edition. The computation and figures work independently of the site. The build_paper.py script regenerates the manuscript and PDF within the website repository; for a standalone copy it writes a local web/ directory.

## Scope

This is an exploratory profile-fit diagnostic, not a particle-physics likelihood, an N-body simulation, a preregistered analysis, a systematic review or a statistical pooling of heterogeneous experiments. Fixed geometry/M/L, independent Gaussian errors and broad halo bounds limit interpretation. The synthetic cutoff removes both inner coverage and points. It does not model an equal-sample-size observing program. Neither cored fits nor fit preference establish self-interactions. This study does not replicate the earlier 149-galaxy multivariate pilot.

## Provenance and rights

Public SPARC data by Lelli, McGaugh & Schombert (2016), AJ 152, 157, https://arxiv.org/abs/1606.09251 . Primary archive https://astroweb.cwru.edu/SPARC/Rotmod_LTG.zip and metadata https://astroweb.cwru.edu/SPARC/SPARC_Lelli2016c.mrt retrieved November 13, 2026 US Eastern. An identical rotation archive was checked against https://zenodo.org/records/16284118/files/Rotmod_LTG.zip . The metadata includes references to original HI/H-alpha observations. The input creators retain their rights; no new license is asserted for their data. All figures in this package are newly generated from the included analysis. No copyrighted paper figures are copied.

Literature search log: targeted searches for LZ 2026 high-energy recoil, LZ solar neutrinos, DESI ultralight axions, SIDM gravothermal collapse and strong lenses, and Euclid DR1-Foundation. Evidence cutoff November 13, 2026. The bibliography records publication status and abstract-only limitations. No cross-experiment significance is pooled. Main numerical analysis is independent of the review sources.
